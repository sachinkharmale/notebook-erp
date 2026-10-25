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


# ── INDEX ────────────────────────────────────
@router.get("/production", response_class=HTMLResponse)
def production_index(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    counts = {
        "indent": query_one("SELECT COUNT(*) AS c FROM indent")["c"],
        "issue": query_one("SELECT COUNT(*) AS c FROM material_issue")["c"],
        "prod": query_one("SELECT COUNT(*) AS c FROM production_entry")["c"],
        "pack": query_one("SELECT COUNT(*) AS c FROM packing_entry")["c"],
        "disp": query_one("SELECT COUNT(*) AS c FROM dispatch_entry")["c"],
    }
    return templates.TemplateResponse("production/index.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "counts": counts,
    })


# ── INDENT ───────────────────────────────────
@router.get("/production/indent", response_class=HTMLResponse)
def indent_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT i.*, w.wos_no,
            (SELECT COUNT(*) FROM indent_line WHERE indent_id = i.id) AS line_count
        FROM indent i JOIN wos w ON w.id = i.wos_id ORDER BY i.id DESC
    """)
    return templates.TemplateResponse("production/indent_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/production/indent/new", response_class=HTMLResponse)
def indent_new(request: Request, wos: int = 0):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    wos_list = query("""
        SELECT w.id, w.wos_no, w.order_qty FROM wos w
        WHERE w.docstatus=1 AND w.wos_status NOT IN ('dispatched','closed','cancelled')
        ORDER BY w.id DESC
    """)
    bom_lines = []
    if wos:
        wb = query_one("SELECT id FROM wos_bom WHERE wos_id=?", (wos,))
        if wb:
            bom_lines = query("""
                SELECT wbl.material_id, wbl.required_qty, m.code AS mcode, m.name AS mname,
                       wbl.uom_id
                FROM wos_bom_line wbl JOIN material m ON m.id = wbl.material_id
                WHERE wbl.wos_bom_id = ?
            """, (wb["id"],))
    departments = query("SELECT id, name FROM department WHERE active=1")
    return templates.TemplateResponse("production/indent_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "wos_list": wos_list, "selected_wos": wos, "bom_lines": bom_lines,
        "departments": departments, "indent_no": next_id("indent"),
        "today": str(date.today()),
    })


@router.post("/production/indent/new")
async def indent_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    indent_no = form.get("indent_no")
    wos_id = int(form.get("wos_id") or 0)
    dept_id = form.get("department_id")
    requestor = form.get("requestor_name", "Production")
    indent_date = form.get("indent_date") or str(date.today())
    mat_ids = form.getlist("material_id")
    qtys = form.getlist("qty")
    wh_ids = form.getlist("warehouse_id")
    uom_ids = form.getlist("uom_id")
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO indent (indent_no, wos_id, department_id, requestor_name, "
                "indent_date, approval_status, docstatus, created_by) "
                "VALUES (?, ?, ?, ?, ?, 'pending', 0, 1)",
                (indent_no, wos_id, int(dept_id) if dept_id else None,
                 requestor, indent_date))
            indent_id = cur.lastrowid
            line_no = 0
            for i, mat in enumerate(mat_ids):
                if not mat:
                    continue
                line_no += 1
                conn.execute(
                    "INSERT INTO indent_line (indent_id, line_no, material_id, "
                    "warehouse_id, uom_id, qty_requested) VALUES (?, ?, ?, ?, ?, ?)",
                    (indent_id, line_no, int(mat),
                     int(wh_ids[i]) if wh_ids[i] else None,
                     int(uom_ids[i]) if uom_ids[i] else 1,
                     float(qtys[i] or 0)))
            conn.commit()
        return RedirectResponse(f"/production/indent/{indent_id}?msg=Created", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/production/indent?msg=Error:+{e}", status_code=303)


@router.get("/production/indent/{indent_id}", response_class=HTMLResponse)
def indent_view(request: Request, indent_id: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    indent = query_one("""
        SELECT i.*, w.wos_no FROM indent i JOIN wos w ON w.id = i.wos_id WHERE i.id=?
    """, (indent_id,))
    if not indent:
        raise HTTPException(404)
    lines = query("""
        SELECT il.*, m.code AS mcode, m.name AS mname,
            COALESCE((SELECT SUM(mil.qty_issued) FROM material_issue_line mil
                      JOIN material_issue mi ON mi.id = mil.material_issue_id AND mi.docstatus=1
                      WHERE mil.indent_line_id = il.id), 0) AS qty_issued
        FROM indent_line il JOIN material m ON m.id = il.material_id
        WHERE il.indent_id = ? ORDER BY il.line_no
    """, (indent_id,))
    return templates.TemplateResponse("production/indent_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "indent": indent, "lines": lines, "msg": msg,
    })


@router.post("/production/indent/{indent_id}/approve")
async def indent_approve(request: Request, indent_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE indent SET approval_status='approved', approved_by=1, "
                "approved_date=CURRENT_TIMESTAMP, docstatus=1 "
                "WHERE id=? AND docstatus=0", (indent_id,))
            conn.execute(
                "UPDATE indent_line SET qty_approved = qty_requested "
                "WHERE indent_id=? AND qty_approved IS NULL", (indent_id,))
            conn.commit()
        return RedirectResponse(f"/production/indent/{indent_id}?msg=Approved", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/production/indent/{indent_id}?msg=Error:+{e}",
                                status_code=303)


# ── MATERIAL ISSUE ───────────────────────────
@router.get("/production/issue", response_class=HTMLResponse)
def issue_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT mi.*, i.indent_no, w.wos_no,
            (SELECT COUNT(*) FROM material_issue_line WHERE material_issue_id=mi.id) AS line_count
        FROM material_issue mi
        JOIN indent i ON i.id = mi.indent_id
        LEFT JOIN wos w ON w.id = mi.wos_id
        ORDER BY mi.id DESC
    """)
    return templates.TemplateResponse("production/issue_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/production/issue/new", response_class=HTMLResponse)
def issue_new(request: Request, indent: int = 0):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    approved_indents = query("""
        SELECT i.id, i.indent_no, w.wos_no FROM indent i
        LEFT JOIN wos w ON w.id = i.wos_id
        WHERE i.docstatus=1 AND i.approval_status IN ('approved','partially_approved')
        ORDER BY i.id DESC
    """)
    warehouses = query("SELECT id, name FROM warehouse WHERE active=1")
    lines = []
    selected_indent = None
    if indent:
        selected_indent = query_one("""
            SELECT i.*, w.wos_no FROM indent i LEFT JOIN wos w ON w.id=i.wos_id
            WHERE i.id=?
        """, (indent,))
        if selected_indent:
            lines = query("""
                SELECT il.*, m.code AS mcode, m.name AS mname,
                    COALESCE((SELECT SUM(mil.qty_issued) FROM material_issue_line mil
                              JOIN material_issue mi ON mi.id=mil.material_issue_id AND mi.docstatus=1
                              WHERE mil.indent_line_id = il.id), 0) AS qty_issued
                FROM indent_line il JOIN material m ON m.id = il.material_id
                WHERE il.indent_id = ? ORDER BY il.line_no
            """, (indent,))
    return templates.TemplateResponse("production/issue_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "approved_indents": approved_indents, "selected_indent": selected_indent,
        "lines": lines, "warehouses": warehouses,
        "issue_no": next_id("material_issue"), "today": str(date.today()),
    })


@router.post("/production/issue/new")
async def issue_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    issue_no = form.get("issue_no")
    indent_id = int(form.get("indent_id") or 0)
    issue_date = form.get("issue_date") or str(date.today())
    issued_to = form.get("issued_to", "Production")
    wh_id = form.get("warehouse_id")
    indent_line_ids = form.getlist("indent_line_id")
    qtys = form.getlist("qty")
    indent = query_one("SELECT wos_id FROM indent WHERE id=?", (indent_id,))
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO material_issue (issue_no, indent_id, wos_id, issue_date, "
                "issued_to, issued_by, warehouse_id, docstatus, created_by) "
                "VALUES (?, ?, ?, ?, ?, 1, ?, 0, 1)",
                (issue_no, indent_id, indent["wos_id"] if indent else None,
                 issue_date, issued_to, int(wh_id) if wh_id else None))
            issue_id = cur.lastrowid
            line_no = 0
            for i, il_id in enumerate(indent_line_ids):
                q = float(qtys[i] or 0)
                if q <= 0:
                    continue
                line_no += 1
                il = query_one(
                    "SELECT material_id, uom_id FROM indent_line WHERE id=?",
                    (int(il_id),))
                conn.execute(
                    "INSERT INTO material_issue_line (material_issue_id, indent_line_id, "
                    "line_no, material_id, uom_id, qty_issued) VALUES (?, ?, ?, ?, ?, ?)",
                    (issue_id, int(il_id), line_no, il["material_id"],
                     il["uom_id"], q))
            conn.commit()
        return RedirectResponse(f"/production/issue/{issue_id}?msg=Created+(draft)",
                                status_code=303)
    except Exception as e:
        return RedirectResponse(f"/production/issue?msg=Error:+{e}", status_code=303)


@router.get("/production/issue/{issue_id}", response_class=HTMLResponse)
def issue_view(request: Request, issue_id: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    issue = query_one("""
        SELECT mi.*, i.indent_no, w.wos_no FROM material_issue mi
        JOIN indent i ON i.id = mi.indent_id
        LEFT JOIN wos w ON w.id = mi.wos_id WHERE mi.id=?
    """, (issue_id,))
    if not issue:
        raise HTTPException(404)
    lines = query("""
        SELECT mil.*, m.code AS mcode, m.name AS mname
        FROM material_issue_line mil JOIN material m ON m.id = mil.material_id
        WHERE mil.material_issue_id=? ORDER BY mil.line_no
    """, (issue_id,))
    return templates.TemplateResponse("production/issue_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "issue": issue, "lines": lines, "msg": msg,
    })


@router.post("/production/issue/{issue_id}/submit")
async def issue_submit(request: Request, issue_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE material_issue SET docstatus=1 WHERE id=? AND docstatus=0",
                (issue_id,))
            conn.commit()
        return RedirectResponse(
            f"/production/issue/{issue_id}?msg=Submitted+-+stock+deducted",
            status_code=303)
    except Exception as e:
        return RedirectResponse(f"/production/issue/{issue_id}?msg=Error:+{e}",
                                status_code=303)


# ── PRODUCTION / PACKING / DISPATCH ─────────
@router.get("/production/entry", response_class=HTMLResponse)
def entry_index(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("production/entry_index.html", {
        "request": request, "user": request.cookies.get("session_user"),
    })


@router.get("/production/entry/new", response_class=HTMLResponse)
def entry_new(request: Request, process: str = "production", wos: int = 0):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    wos_list = query("""
        SELECT w.id, w.wos_no, w.order_qty, w.sku_id FROM wos w
        WHERE w.docstatus=1 AND w.wos_status NOT IN ('dispatched','closed','cancelled')
        ORDER BY w.id DESC
    """)
    prefix_map = {"production": "production_entry", "packing": "packing_entry",
                  "dispatch": "dispatch_entry"}
    if process not in prefix_map:
        process = "production"
    no = next_id(prefix_map[process])
    return templates.TemplateResponse("production/entry_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "wos_list": wos_list, "selected_wos": wos, "process": process, "no": no,
        "today": str(date.today()),
    })


@router.post("/production/entry/new")
async def entry_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    process = form.get("process", "production")
    wos_id = int(form.get("wos_id") or 0)
    entry_date = form.get("entry_date") or str(date.today())
    try:
        with get_conn() as conn:
            if process == "production":
                conn.execute(
                    "INSERT INTO production_entry (production_no, wos_id, production_date, "
                    "machine_name, producer, qty_produced, wastage_qty, docstatus, created_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)",
                    (form.get("entry_no"), wos_id, entry_date,
                     form.get("machine_name"), form.get("producer"),
                     float(form.get("qty") or 0),
                     float(form.get("wastage") or 0)))
            elif process == "packing":
                conn.execute(
                    "INSERT INTO packing_entry (packing_no, wos_id, packing_date, qty_packed, "
                    "master_cases, packed_by, docstatus, created_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, 1, 1)",
                    (form.get("entry_no"), wos_id, entry_date,
                     float(form.get("qty") or 0),
                     int(form.get("master_cases") or 0) or None,
                     form.get("producer")))
            else:
                conn.execute(
                    "INSERT INTO dispatch_entry (dispatch_no, wos_id, dispatch_date, "
                    "qty_dispatched, master_cases, vehicle_no, transporter_name, lr_no, "
                    "driver_name, dispatch_status, docstatus, created_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'partial', 1, 1)",
                    (form.get("entry_no"), wos_id, entry_date,
                     float(form.get("qty") or 0),
                     int(form.get("master_cases") or 0) or None,
                     form.get("vehicle_no"), form.get("transporter_name"),
                     form.get("lr_no"), form.get("driver_name")))
            conn.commit()
        return RedirectResponse(f"/production/entry?msg=Entry+created", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/production/entry/new?process={process}&msg=Error:+{e}",
                                status_code=303)
