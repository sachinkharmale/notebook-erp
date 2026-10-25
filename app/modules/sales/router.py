from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...config import BASE_DIR
from ...db import get_conn, query, query_one
from ...core.naming import next_id
from ..masters.router import require_session

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _po_list():
    return query("""
        SELECT cp.*, c.name AS customer_name,
            (SELECT COUNT(*) FROM customer_po_line WHERE customer_po_id = cp.id) AS line_count,
            (SELECT COALESCE(SUM(qty),0) FROM customer_po_line WHERE customer_po_id = cp.id) AS total_qty
        FROM customer_po cp JOIN customer c ON c.id = cp.customer_id
        ORDER BY cp.id DESC
    """)


@router.get("/sales", response_class=HTMLResponse)
def sales_index(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    po_count = query_one("SELECT COUNT(*) AS c FROM customer_po")["c"]
    wos_count = query_one("SELECT COUNT(*) AS c FROM wos")["c"]
    return templates.TemplateResponse("sales/index.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "po_count": po_count, "wos_count": wos_count,
    })


@router.get("/sales/customer-po", response_class=HTMLResponse)
def po_list_page(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("sales/po_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": _po_list(), "msg": msg,
    })


@router.get("/sales/customer-po/new", response_class=HTMLResponse)
def po_new(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    customers = query("SELECT id, name FROM customer WHERE active=1 ORDER BY name")
    skus = query("SELECT id, code, name FROM sku WHERE active=1 ORDER BY code")
    return templates.TemplateResponse("sales/po_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "customers": customers, "skus": skus,
        "po_no": next_id("customer_po"), "row": None, "lines": [{}], "error": None,
    })


@router.post("/sales/customer-po/new")
async def po_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    po_no = form.get("po_no")
    customer_id = int(form.get("customer_id") or 0)
    po_date = form.get("po_date")
    status = form.get("status", "draft")
    sku_ids = form.getlist("sku_id")
    qtys = form.getlist("qty")
    rates = form.getlist("rate")
    dd = form.getlist("delivery_date")

    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO customer_po (po_no, customer_id, po_date, status, docstatus, created_by) "
                "VALUES (?, ?, ?, ?, ?, 1)",
                (po_no, customer_id, po_date, status, 1 if status != "draft" else 0),
            )
            po_id = cur.lastrowid
            line_no = 0
            for i, sku in enumerate(sku_ids):
                if not sku:
                    continue
                line_no += 1
                conn.execute(
                    "INSERT INTO customer_po_line "
                    "(customer_po_id, line_no, sku_id, qty, rate, delivery_date) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (po_id, line_no, int(sku), float(qtys[i] or 0),
                     float(rates[i] or 0) if rates[i] else None, dd[i] or None),
                )
            conn.commit()
        return RedirectResponse(f"/sales/customer-po/{po_id}?msg=Created", status_code=303)
    except Exception as e:
        customers = query("SELECT id, name FROM customer WHERE active=1")
        skus = query("SELECT id, code, name FROM sku WHERE active=1")
        return templates.TemplateResponse("sales/po_form.html", {
            "request": request, "user": request.cookies.get("session_user"),
            "customers": customers, "skus": skus, "po_no": po_no,
            "row": dict(form), "lines": [{}], "error": str(e),
        })


@router.get("/sales/customer-po/{po_id}", response_class=HTMLResponse)
def po_view(request: Request, po_id: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    po = query_one("""
        SELECT cp.*, c.name AS customer_name FROM customer_po cp
        JOIN customer c ON c.id = cp.customer_id WHERE cp.id = ?
    """, (po_id,))
    if not po:
        raise HTTPException(404)
    lines = query("""
        SELECT cpl.*, s.code AS sku_code, s.name AS sku_name,
            (SELECT w.wos_no FROM wos w WHERE w.po_line_id = cpl.id LIMIT 1) AS wos_no,
            (SELECT w.id FROM wos w WHERE w.po_line_id = cpl.id LIMIT 1) AS wos_id
        FROM customer_po_line cpl JOIN sku s ON s.id = cpl.sku_id
        WHERE cpl.customer_po_id = ? ORDER BY cpl.line_no
    """, (po_id,))
    return templates.TemplateResponse("sales/po_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "po": po, "lines": lines, "msg": msg,
    })


@router.post("/sales/customer-po/line/{line_id}/create-wos")
async def create_wos(request: Request, line_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    line = query_one("""
        SELECT cpl.*, cp.customer_id FROM customer_po_line cpl
        JOIN customer_po cp ON cp.id = cpl.customer_po_id WHERE cpl.id = ?
    """, (line_id,))
    if not line:
        raise HTTPException(404)
    if query_one("SELECT id FROM wos WHERE po_line_id = ?", (line_id,)):
        return RedirectResponse(
            f"/sales/customer-po/{line['customer_po_id']}?msg=WOS+already+exists",
            status_code=303)
    wos_no = next_id("wos")
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO wos (wos_no, po_line_id, customer_id, sku_id, order_qty, "
                "ship_date, wos_status, docstatus, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, 'pending_shipment', 1, 1)",
                (wos_no, line_id, line["customer_id"], line["sku_id"],
                 line["qty"], line["delivery_date"]),
            )
            conn.commit()
        return RedirectResponse(
            f"/sales/customer-po/{line['customer_po_id']}?msg=WOS+{wos_no}+created",
            status_code=303)
    except Exception as e:
        return RedirectResponse(
            f"/sales/customer-po/{line['customer_po_id']}?msg=Error:+{e}",
            status_code=303)


@router.get("/sales/wos", response_class=HTMLResponse)
def wos_list_page(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT w.*, c.name AS customer_name, s.code AS sku_code, s.name AS sku_name,
            COALESCE((SELECT SUM(qty_produced) FROM production_entry WHERE wos_id=w.id AND docstatus=1),0) AS qty_produced,
            COALESCE((SELECT SUM(qty_packed) FROM packing_entry WHERE wos_id=w.id AND docstatus=1),0) AS qty_packed,
            COALESCE((SELECT SUM(qty_dispatched) FROM dispatch_entry WHERE wos_id=w.id AND docstatus=1),0) AS qty_dispatched
        FROM wos w JOIN customer c ON c.id = w.customer_id JOIN sku s ON s.id = w.sku_id
        ORDER BY w.id DESC
    """)
    return templates.TemplateResponse("sales/wos_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/sales/wos/{wos_id}", response_class=HTMLResponse)
def wos_view(request: Request, wos_id: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    wos = query_one("""
        SELECT w.*, c.name AS customer_name, s.code AS sku_code, s.name AS sku_name,
               s.spec_size, s.spec_pages, s.spec_ruling, s.spec_binding
        FROM wos w JOIN customer c ON c.id = w.customer_id JOIN sku s ON s.id = w.sku_id
        WHERE w.id = ?
    """, (wos_id,))
    if not wos:
        raise HTTPException(404)
    po_info = query_one("""
        SELECT cp.po_no, cpl.line_no FROM customer_po_line cpl
        JOIN customer_po cp ON cp.id = cpl.customer_po_id WHERE cpl.id = ?
    """, (wos["po_line_id"],))
    rollup = query_one("SELECT * FROM v_wos_rollup WHERE wos_id = ?", (wos_id,)) or {
        "qty_produced": 0, "qty_packed": 0, "qty_dispatched": 0,
        "qty_balance": wos["order_qty"], "wos_status": wos["wos_status"]}
    bom = query_one("""
        SELECT wb.*, bt.bom_id FROM wos_bom wb
        JOIN bom_template bt ON bt.id = wb.bom_template_id WHERE wb.wos_id = ?
    """, (wos_id,))
    bom_lines = []
    if bom:
        bom_lines = query("""
            SELECT wbl.*, m.code AS mcode, m.name AS mname
            FROM wos_bom_line wbl JOIN material m ON m.id = wbl.material_id
            WHERE wbl.wos_bom_id = ? ORDER BY wbl.id
        """, (bom["id"],))
    matching_boms = query("""
        SELECT * FROM bom_template
        WHERE docstatus=1 AND active=1
          AND (size = ? OR size IS NULL) AND (pages = ? OR pages IS NULL)
          AND (ruling_type = ? OR ruling_type IS NULL)
          AND (binding_type = ? OR binding_type IS NULL)
        ORDER BY id DESC
    """, (wos["spec_size"], wos["spec_pages"], wos["spec_ruling"], wos["spec_binding"]))
    indents = query("SELECT * FROM indent WHERE wos_id=? ORDER BY id DESC", (wos_id,))
    prod = query("SELECT * FROM production_entry WHERE wos_id=? ORDER BY id DESC", (wos_id,))
    pack = query("SELECT * FROM packing_entry WHERE wos_id=? ORDER BY id DESC", (wos_id,))
    disp = query("SELECT * FROM dispatch_entry WHERE wos_id=? ORDER BY id DESC", (wos_id,))
    return templates.TemplateResponse("sales/wos_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "wos": wos, "po_info": po_info, "rollup": rollup, "msg": msg,
        "bom": bom, "bom_lines": bom_lines, "matching_boms": matching_boms,
        "indents": indents, "prod": prod, "pack": pack, "disp": disp,
    })


@router.post("/sales/wos/{wos_id}/match-bom")
async def wos_match_bom(request: Request, wos_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    bt_id = int(form.get("bom_template_id") or 0)
    wos = query_one("SELECT * FROM wos WHERE id=?", (wos_id,))
    if not wos:
        raise HTTPException(404)
    if query_one("SELECT id FROM wos_bom WHERE wos_id=?", (wos_id,)):
        return RedirectResponse(f"/sales/wos/{wos_id}?msg=BOM+already+matched", status_code=303)
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO wos_bom (wos_id, bom_template_id, matched_on_snapshot, created_by) "
                "VALUES (?, ?, 'matched', 1)", (wos_id, bt_id))
            wb_id = cur.lastrowid
            lines = conn.execute(
                "SELECT * FROM bom_template_line WHERE bom_template_id=? AND active=1",
                (bt_id,)).fetchall()
            for line in lines:
                required = line["effective_qty_per_1000"] * wos["order_qty"] / 1000.0
                conn.execute(
                    "INSERT INTO wos_bom_line (wos_bom_id, material_id, uom_id, "
                    "base_qty_per_1000, wastage_pct, loss_pct, effective_qty_per_1000, "
                    "order_qty_basis, required_qty, spec_signature) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (wb_id, line["material_id"], line["uom_id"],
                     line["base_qty_per_1000"], line["wastage_pct"], line["loss_pct"],
                     line["effective_qty_per_1000"], wos["order_qty"], required,
                     line["spec_signature"]))
            conn.execute(
                "UPDATE wos SET wos_status='bom_created' WHERE id=? AND wos_status='pending_shipment'",
                (wos_id,))
            conn.commit()
        return RedirectResponse(
            f"/sales/wos/{wos_id}?msg=BOM+matched+({len(lines)}+lines)", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/sales/wos/{wos_id}?msg=Error:+{e}", status_code=303)
