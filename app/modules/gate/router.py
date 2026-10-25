from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date, datetime
from ...config import BASE_DIR
from ...db import get_conn, query, query_one
from ...core.naming import next_id
from ..masters.router import require_session

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/gate", response_class=HTMLResponse)
def gate_index(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    counts = {
        "vehicles": query_one("SELECT COUNT(*) AS c FROM vehicle_visit")["c"],
        "visitors": query_one("SELECT COUNT(*) AS c FROM visitor_visit")["c"],
    }
    return templates.TemplateResponse("gate/index.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "counts": counts,
    })


# ── VEHICLE VISITS ───────────────────────────
@router.get("/gate/vehicle", response_class=HTMLResponse)
def vehicle_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("""
        SELECT * FROM vehicle_visit ORDER BY id DESC LIMIT 200
    """)
    return templates.TemplateResponse("gate/vehicle_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/gate/vehicle/new", response_class=HTMLResponse)
def vehicle_new(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("gate/vehicle_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "no": next_id("vehicle_visit"), "today": str(date.today()),
        "now": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "row": None,
    })


@router.post("/gate/vehicle/new")
async def vehicle_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    f = await request.form()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO vehicle_visit (visit_no, visit_date, load_type, vehicle_number, "
                "vehicle_code, driver_name, driver_licence, driver_mobile, party_name, "
                "item_reference, inward_challan_no, outward_challan_no, container_no, "
                "container_seal_no, rfid_seal_no, in_time, first_weight, last_weight, "
                "out_time, weighbridge_station, weight_unit, remarks, docstatus, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'kg', ?, 1, 1)",
                (f.get("visit_no"), f.get("visit_date"), f.get("load_type"),
                 f.get("vehicle_number"), f.get("vehicle_code"), f.get("driver_name"),
                 f.get("driver_licence"), f.get("driver_mobile"), f.get("party_name"),
                 f.get("item_reference"), f.get("inward_challan_no"),
                 f.get("outward_challan_no"), f.get("container_no"),
                 f.get("container_seal_no"), f.get("rfid_seal_no"),
                 f.get("in_time"), float(f.get("first_weight") or 0) or None,
                 float(f.get("last_weight") or 0) or None, f.get("out_time"),
                 f.get("weighbridge_station"), f.get("remarks")))
            conn.commit()
        return RedirectResponse("/gate/vehicle?msg=Created", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/gate/vehicle?msg=Error:+{e}", status_code=303)


@router.get("/gate/vehicle/{vid}", response_class=HTMLResponse)
def vehicle_view(request: Request, vid: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    row = query_one("SELECT * FROM vehicle_visit WHERE id=?", (vid,))
    if not row:
        raise HTTPException(404)
    return templates.TemplateResponse("gate/vehicle_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "row": row, "msg": msg,
    })


# ── VISITOR VISITS ───────────────────────────
@router.get("/gate/visitor", response_class=HTMLResponse)
def visitor_list(request: Request, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    rows = query("SELECT * FROM visitor_visit ORDER BY id DESC LIMIT 200")
    return templates.TemplateResponse("gate/visitor_list.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "rows": rows, "msg": msg,
    })


@router.get("/gate/visitor/new", response_class=HTMLResponse)
def visitor_new(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    departments = query("SELECT id, name FROM department WHERE active=1")
    return templates.TemplateResponse("gate/visitor_form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "no": next_id("visitor_visit"), "departments": departments,
        "now": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "row": None,
    })


@router.post("/gate/visitor/new")
async def visitor_create(request: Request):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    f = await request.form()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO visitor_visit (visit_no, in_time, out_time, visitor_name, "
                "company_name, coming_from, mobile, whom_to_meet, host_department_id, "
                "purpose, items_carried, id_proof_type, id_proof_number, vehicle_number, "
                "vehicle_type, badge_no, remarks, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (f.get("visit_no"), f.get("in_time"), f.get("out_time"),
                 f.get("visitor_name"), f.get("company_name"), f.get("coming_from"),
                 f.get("mobile"), f.get("whom_to_meet"),
                 int(f.get("host_department_id")) if f.get("host_department_id") else None,
                 f.get("purpose"), f.get("items_carried"), f.get("id_proof_type"),
                 f.get("id_proof_number"), f.get("vehicle_number"),
                 f.get("vehicle_type"), f.get("badge_no"), f.get("remarks")))
            conn.commit()
        return RedirectResponse("/gate/visitor?msg=Created", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/gate/visitor?msg=Error:+{e}", status_code=303)


@router.get("/gate/visitor/{vid}", response_class=HTMLResponse)
def visitor_view(request: Request, vid: int, msg: str = ""):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    row = query_one("SELECT * FROM visitor_visit WHERE id=?", (vid,))
    if not row:
        raise HTTPException(404)
    return templates.TemplateResponse("gate/visitor_view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "row": row, "msg": msg,
    })
