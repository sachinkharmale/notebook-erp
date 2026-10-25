from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date
from ...config import BASE_DIR
from ...db import get_conn, query, query_one
from ...core.naming import next_id
from ..masters.router import require_session

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/finance", response_class=HTMLResponse)
def finance_index(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    si_ar = query_one("SELECT COALESCE(SUM(balance),0) AS v FROM v_sales_invoice_status WHERE docstatus=1 AND balance > 0")["v"]
    pi_ap = query_one("SELECT COALESCE(SUM(balance),0) AS v FROM v_purchase_invoice_status WHERE docstatus=1 AND balance > 0")["v"]
    counts = {
        "si": query_one("SELECT COUNT(*) AS c FROM sales_invoice")["c"],
        "pi": query_one("SELECT COUNT(*) AS c FROM purchase_invoice")["c"],
        "pay": query_one("SELECT COUNT(*) AS c FROM payment_entry")["c"],
    }
    return templates.TemplateResponse("finance/index.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "counts": counts, "ar": si_ar, "ap": pi_ap,
    })


# ── SALES INVOICES ───────────────────────────
@router.get("/finance/sales-invoice", response_class=HTMLResponse)
def si_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT vis.*, c.name AS customer_name
        FROM v_sales_invoice_status vis JOIN customer c ON c.id = vis.customer_id
        ORDER BY vis.id DESC
    """)
    return templates.TemplateResponse("finance/si_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/finance/sales-invoice/new", response_class=HTMLResponse)
def si_new(request: Request, dispatch: int = 0):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    customers = query("SELECT id, name FROM customer WHERE active=1")
    dispatches = query("""
        SELECT de.id, de.dispatch_no, de.qty_dispatched, de.dispatch_date,
               w.customer_id, w.sku_id, s.code AS sku_code, s.name AS sku_name,
               cpl.rate
        FROM dispatch_entry de
        JOIN wos w ON w.id = de.wos_id
        JOIN sku s ON s.id = w.sku_id
        JOIN customer_po_line cpl ON cpl.id = w.po_line_id
        WHERE de.docstatus=1
          AND NOT EXISTS (SELECT 1 FROM sales_invoice si WHERE si.dispatch_id = de.id)
        ORDER BY de.id DESC
    """)
    prefill = None
    if dispatch:
        prefill = next((d for d in dispatches if d["id"] == dispatch), None)
    return templates.TemplateResponse("finance/si_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "customers": customers, "dispatches": dispatches,
        "prefill": prefill, "no": next_id("sales_invoice"),
        "today": str(date.today()),
    })


@router.post("/finance/sales-invoice/new")
async def si_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    f = await request.form()
    try:
        qty = float(f.get("qty") or 0)
        rate = float(f.get("rate") or 0)
        tax_rate = float(f.get("tax_rate") or 18)
        subtotal = qty * rate
        tax_amount = subtotal * tax_rate / 100
        total = subtotal + tax_amount
        dispatch_id = int(f.get("dispatch_id")) if f.get("dispatch_id") else None
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO sales_invoice (invoice_no, customer_id, dispatch_id, "
                "invoice_date, due_date, subtotal, tax_rate, tax_amount, total_amount, "
                "status, docstatus) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'sent', 1)",
                (f.get("invoice_no"), int(f.get("customer_id")), dispatch_id,
                 f.get("invoice_date"), f.get("due_date"),
                 subtotal, tax_rate, tax_amount, total))
            si_id = cur.lastrowid
            sku_id = None
            wos_id = None
            if dispatch_id:
                d = conn.execute("SELECT wos_id FROM dispatch_entry WHERE id=?", (dispatch_id,)).fetchone()
                if d:
                    wos_id = d["wos_id"]
                    w = conn.execute("SELECT sku_id FROM wos WHERE id=?", (wos_id,)).fetchone()
                    sku_id = w["sku_id"] if w else None
            conn.execute(
                "INSERT INTO sales_invoice_line (sales_invoice_id, line_no, sku_id, "
                "wos_id, description, qty, rate, amount) VALUES (?, 1, ?, ?, ?, ?, ?, ?)",
                (si_id, sku_id, wos_id, f.get("description"), qty, rate, subtotal))
            conn.commit()
        return RedirectResponse(f"/finance/sales-invoice/{si_id}?msg=Created", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/finance/sales-invoice?msg=Error:+{e}", status_code=303)


@router.get("/finance/sales-invoice/{si_id}", response_class=HTMLResponse)
def si_view(request: Request, si_id: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    si = query_one("""
        SELECT vis.*, c.name AS customer_name FROM v_sales_invoice_status vis
        JOIN customer c ON c.id = vis.customer_id WHERE vis.id = ?
    """, (si_id,))
    if not si:
        raise HTTPException(404)
    lines = query("""
        SELECT sil.*, s.code AS sku_code, s.name AS sku_name, w.wos_no
        FROM sales_invoice_line sil
        LEFT JOIN sku s ON s.id = sil.sku_id
        LEFT JOIN wos w ON w.id = sil.wos_id
        WHERE sil.sales_invoice_id = ?
    """, (si_id,))
    allocs = query("""
        SELECT pa.*, pe.payment_no, pe.payment_date, pe.payment_mode
        FROM payment_allocation pa JOIN payment_entry pe ON pe.id = pa.payment_entry_id
        WHERE pa.invoice_type = 'sales_invoice' AND pa.invoice_id = ?
    """, (si_id,))
    return templates.TemplateResponse("finance/si_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "si": si, "lines": lines, "allocs": allocs, "msg": msg,
    })


# ── PURCHASE INVOICES ────────────────────────
@router.get("/finance/purchase-invoice", response_class=HTMLResponse)
def pi_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT vpi.*, s.name AS supplier_name
        FROM v_purchase_invoice_status vpi JOIN supplier s ON s.id = vpi.supplier_id
        ORDER BY vpi.id DESC
    """)
    return templates.TemplateResponse("finance/pi_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/finance/purchase-invoice/{pi_id}", response_class=HTMLResponse)
def pi_view(request: Request, pi_id: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    pi = query_one("""
        SELECT vpi.*, s.name AS supplier_name FROM v_purchase_invoice_status vpi
        JOIN supplier s ON s.id = vpi.supplier_id WHERE vpi.id = ?
    """, (pi_id,))
    if not pi:
        raise HTTPException(404)
    lines = query("""
        SELECT pil.*, m.code AS material_code, m.name AS material_name
        FROM purchase_invoice_line pil
        LEFT JOIN material m ON m.id = pil.material_id
        WHERE pil.purchase_invoice_id = ?
    """, (pi_id,))
    return templates.TemplateResponse("finance/pi_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "pi": pi, "lines": lines, "msg": msg,
    })


# ── PAYMENTS ─────────────────────────────────
@router.get("/finance/payment", response_class=HTMLResponse)
def payment_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT pe.*,
            CASE pe.party_type
                WHEN 'customer' THEN (SELECT name FROM customer WHERE id = pe.party_id)
                WHEN 'supplier' THEN (SELECT name FROM supplier WHERE id = pe.party_id)
            END AS party_name
        FROM payment_entry pe ORDER BY pe.id DESC
    """)
    return templates.TemplateResponse("finance/payment_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/finance/payment/new", response_class=HTMLResponse)
def payment_new(request: Request, ptype: str = "receipt", party_type: str = "customer"):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    customers = query("SELECT id, name FROM customer WHERE active=1")
    suppliers = query("SELECT id, name FROM supplier WHERE active=1")
    return templates.TemplateResponse("finance/payment_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "no": next_id("payment_entry"), "today": str(date.today()),
        "customers": customers, "suppliers": suppliers,
        "ptype": ptype, "party_type": party_type,
    })


@router.post("/finance/payment/new")
async def payment_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    f = await request.form()
    try:
        payment_type = f.get("payment_type")
        party_type = "customer" if payment_type == "receipt" else "supplier"
        party_id = int(f.get("party_id"))
        amount = float(f.get("amount") or 0)
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO payment_entry (payment_no, payment_type, party_type, "
                "party_id, payment_date, amount, payment_mode, reference_no, "
                "remarks, docstatus) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (f.get("payment_no"), payment_type, party_type, party_id,
                 f.get("payment_date"), amount, f.get("payment_mode"),
                 f.get("reference_no"), f.get("remarks")))
            pay_id = cur.lastrowid
            invoice_id = f.get("invoice_id")
            if invoice_id:
                inv_type = "sales_invoice" if payment_type == "receipt" else "purchase_invoice"
                conn.execute(
                    "INSERT INTO payment_allocation (payment_entry_id, invoice_type, "
                    "invoice_id, allocated_amount) VALUES (?, ?, ?, ?)",
                    (pay_id, inv_type, int(invoice_id), amount))
            conn.commit()
        return RedirectResponse("/finance/payment?msg=Created", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/finance/payment?msg=Error:+{e}", status_code=303)


@router.get("/api/finance/open-invoices")
def open_invoices(request: Request, party_type: str = "customer", party_id: int = 0):
    if not require_session(request):
        raise HTTPException(401)
    if party_type == "customer":
        rows = query("""
            SELECT id, invoice_no AS no, invoice_date AS date, balance
            FROM v_sales_invoice_status
            WHERE customer_id = ? AND docstatus=1 AND balance > 0.01
            ORDER BY invoice_date
        """, (party_id,))
    else:
        rows = query("""
            SELECT id, invoice_no AS no, invoice_date AS date, balance
            FROM v_purchase_invoice_status
            WHERE supplier_id = ? AND docstatus=1 AND balance > 0.01
            ORDER BY invoice_date
        """, (party_id,))
    return [dict(r) for r in rows]
