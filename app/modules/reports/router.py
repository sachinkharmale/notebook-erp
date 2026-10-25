from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date, datetime
from ...config import BASE_DIR
from ...db import query, query_one
from ..masters.router import require_session

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _aging(rows):
    today = date.today()
    out = []
    for r in rows:
        d = dict(r)
        due = d.get("due_date")
        if due:
            try:
                days = (today - datetime.strptime(due, "%Y-%m-%d").date()).days
            except Exception:
                days = 0
        else:
            days = 0
        d["days_overdue"] = days
        if days <= 0:
            d["bucket"] = "current"
        elif days <= 30:
            d["bucket"] = "0_30"
        elif days <= 60:
            d["bucket"] = "31_60"
        elif days <= 90:
            d["bucket"] = "61_90"
        else:
            d["bucket"] = "90_plus"
        out.append(d)
    return out


def _bucket_totals(rows):
    totals = {"current": 0, "0_30": 0, "31_60": 0, "61_90": 0, "90_plus": 0}
    for r in rows:
        b = r.get("bucket", "current")
        totals[b] += r.get("balance", 0) or 0
    return totals


@router.get("/reports", response_class=HTMLResponse)
def reports_index(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    counts = {
        "wos_open": query_one("SELECT COUNT(*) AS c FROM wos WHERE wos_status NOT IN ('dispatched','closed','cancelled') AND docstatus=1")["c"],
        "stock_value": query_one("SELECT COALESCE(SUM(stock_value),0) AS v FROM v_stock_balance")["v"],
        "ar": query_one("SELECT COALESCE(SUM(balance),0) AS v FROM v_sales_invoice_status WHERE docstatus=1 AND balance > 0")["v"],
        "ap": query_one("SELECT COALESCE(SUM(balance),0) AS v FROM v_purchase_invoice_status WHERE docstatus=1 AND balance > 0")["v"],
    }
    return templates.TemplateResponse("reports/index.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "counts": counts,
    })


# ── WOS TRACKER ──────────────────────────────
@router.get("/reports/wos-tracker", response_class=HTMLResponse)
def wos_tracker(request: Request, status: str = "", q: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    sql = """
        SELECT vr.*, c.name AS customer_name, s.code AS sku_code, w.ship_date
        FROM v_wos_rollup vr
        JOIN wos w ON w.id = vr.wos_id
        JOIN customer c ON c.id = w.customer_id
        JOIN sku s ON s.id = w.sku_id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND vr.wos_status = ?"
        params.append(status)
    if q:
        sql += " AND (vr.wos_no LIKE ? OR c.name LIKE ? OR s.code LIKE ?)"
        params.extend([f"%{q}%"] * 3)
    sql += " ORDER BY w.ship_date IS NULL, w.ship_date ASC, w.id DESC"
    rows = query(sql, tuple(params))
    status_counts = {}
    for r in query("SELECT wos_status FROM wos WHERE docstatus=1"):
        status_counts[r["wos_status"]] = status_counts.get(r["wos_status"], 0) + 1
    return templates.TemplateResponse("reports/wos_tracker.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "status_counts": status_counts, "status": status, "q": q,
    })


# ── STOCK BALANCE ─────────────────────────────
@router.get("/reports/stock-balance", response_class=HTMLResponse)
def stock_balance(request: Request, wh: str = "", cat: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    sql = """
        SELECT vb.*, m.code AS material_code, m.name AS material_name,
               m.category, m.material_group, w.name AS warehouse_name
        FROM v_stock_balance vb
        JOIN material m ON m.id = vb.material_id
        JOIN warehouse w ON w.id = vb.warehouse_id
        WHERE vb.qty_balance != 0
    """
    params = []
    if wh:
        sql += " AND vb.warehouse_id = ?"
        params.append(int(wh))
    if cat:
        sql += " AND m.category = ?"
        params.append(cat)
    sql += " ORDER BY m.code"
    rows = query(sql, tuple(params))
    total_value = sum((r["stock_value"] or 0) for r in rows)
    warehouses = query("SELECT id, name FROM warehouse WHERE active=1")
    return templates.TemplateResponse("reports/stock_balance.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "total_value": total_value, "warehouses": warehouses,
        "wh": wh, "cat": cat,
    })


# ── MRP ───────────────────────────────────────
@router.get("/reports/mrp", response_class=HTMLResponse)
def mrp(request: Request, cat: str = "", action: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    sql = "SELECT * FROM v_material_requirement WHERE 1=1"
    params = []
    if cat:
        sql += " AND material_category = ?"
        params.append(cat)
    if action == "procure":
        sql += " AND qty_to_procure > 0"
    sql += " ORDER BY earliest_need_by IS NULL, earliest_need_by ASC, material_code"
    rows = query(sql, tuple(params))
    total_shortage = sum((r["qty_to_procure"] or 0) for r in rows)
    return templates.TemplateResponse("reports/mrp.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "total_shortage": total_shortage, "cat": cat, "action": action,
    })


# ── INDENT STATUS ─────────────────────────────
@router.get("/reports/indent-status", response_class=HTMLResponse)
def indent_status(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT vir.*, i.indent_no, m.code AS material_code, m.name AS material_name,
               i.wos_id, w.wos_no
        FROM v_indent_rollup vir
        JOIN indent_line il ON il.id = vir.indent_line_id
        JOIN indent i ON i.id = il.indent_id
        JOIN material m ON m.id = vir.material_id
        LEFT JOIN wos w ON w.id = i.wos_id
        WHERE i.docstatus = 1
        ORDER BY i.id DESC, vir.indent_line_id
    """)
    return templates.TemplateResponse("reports/indent_status.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows,
    })


# ── PO TRACKER ────────────────────────────────
@router.get("/reports/po-tracker", response_class=HTMLResponse)
def po_tracker(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT vpr.*, sp.po_no, sp.status AS po_status, s.name AS supplier_name,
               m.code AS material_code, m.name AS material_name
        FROM v_supplier_po_rollup vpr
        JOIN supplier_po sp ON sp.id = vpr.supplier_po_id
        JOIN supplier s ON s.id = sp.supplier_id
        JOIN material m ON m.id = vpr.material_id
        WHERE sp.docstatus = 1
        ORDER BY sp.id DESC, vpr.po_line_id
    """)
    return templates.TemplateResponse("reports/po_tracker.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows,
    })


# ── AR AGING ──────────────────────────────────
@router.get("/reports/ar-aging", response_class=HTMLResponse)
def ar_aging(request: Request, bucket: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = _aging(query("""
        SELECT vis.*, c.name AS customer_name
        FROM v_sales_invoice_status vis
        JOIN customer c ON c.id = vis.customer_id
        WHERE vis.docstatus = 1 AND vis.balance > 0.01
        ORDER BY vis.due_date
    """))
    if bucket:
        rows = [r for r in rows if r["bucket"] == bucket]
    totals = _bucket_totals(_aging(query("""
        SELECT vis.* FROM v_sales_invoice_status vis
        WHERE vis.docstatus = 1 AND vis.balance > 0.01
    """)))
    return templates.TemplateResponse("reports/ar_aging.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "totals": totals, "bucket": bucket,
    })


# ── AP AGING ──────────────────────────────────
@router.get("/reports/ap-aging", response_class=HTMLResponse)
def ap_aging(request: Request, bucket: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = _aging(query("""
        SELECT vpi.*, s.name AS supplier_name
        FROM v_purchase_invoice_status vpi
        JOIN supplier s ON s.id = vpi.supplier_id
        WHERE vpi.docstatus = 1 AND vpi.balance > 0.01
        ORDER BY vpi.due_date
    """))
    if bucket:
        rows = [r for r in rows if r["bucket"] == bucket]
    totals = _bucket_totals(_aging(query("""
        SELECT vpi.* FROM v_purchase_invoice_status vpi
        WHERE vpi.docstatus = 1 AND vpi.balance > 0.01
    """)))
    return templates.TemplateResponse("reports/ap_aging.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "totals": totals, "bucket": bucket,
    })
