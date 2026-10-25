from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from ...config import BASE_DIR
from ...db import get_conn, query, query_one, table_count
from ...auth import hash_password
from .config import MASTERS

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def require_session(request: Request):
    user = request.cookies.get("session_user")
    if not user:
        return None
    return user


def row_to_dict(row):
    if row is None:
        return {}
    try:
        return {k: row[k] for k in row.keys()}
    except AttributeError:
        return dict(row)


def get_ref_options(field):
    if field.get("type") != "ref":
        return None
    ref_table = field["ref_table"]
    ref_label = field.get("ref_label", "name")
    try:
        return query(f"SELECT id, {ref_label} AS label FROM {ref_table} "
                     f"WHERE active=1 ORDER BY {ref_label}")
    except sqlite3.Error:
        return []


def coerce_field(field, value):
    t = field.get("type", "text")
    if t == "password":
        return value if value else None
    if t in ("number", "ref"):
        return float(value) if value not in (None, "") else None
    if t == "integer":
        return int(float(value)) if value not in (None, "") else None
    if t == "checkbox":
        return 1 if value in ("on", "1", "true") else 0
    return value if value not in (None, "") else None


@router.get("/masters", response_class=HTMLResponse)
def masters_index(request: Request):
    user = require_session(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    counts = {k: table_count(v["table"]) for k, v in MASTERS.items()}
    return templates.TemplateResponse("masters/index.html", {
        "request": request, "user": user, "masters": MASTERS, "counts": counts,
    })


@router.get("/masters/{entity}", response_class=HTMLResponse)
def masters_list(request: Request, entity: str, q: str = "", msg: str = "", error: str = ""):
    user = require_session(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    sql = f"SELECT * FROM {cfg['table']}"
    params = ()
    if q and cfg.get("search_fields"):
        where = " OR ".join([f"{f} LIKE ?" for f in cfg["search_fields"]])
        sql += f" WHERE {where}"
        params = tuple([f"%{q}%"] * len(cfg["search_fields"]))
    sql += " ORDER BY id DESC LIMIT 200"
    rows = [row_to_dict(r) for r in query(sql, params)]
    return templates.TemplateResponse("masters/list.html", {
        "request": request, "user": user, "entity": entity, "cfg": cfg,
        "rows": rows, "q": q, "msg": msg, "error": error,
    })


def _render_form(request, entity, cfg, row, mode, error=None):
    ref_options = {f["key"]: get_ref_options(f) for f in cfg["fields"] if f.get("type") == "ref"}
    return templates.TemplateResponse("masters/form.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "entity": entity, "cfg": cfg, "row": row,
        "ref_options": ref_options, "mode": mode, "error": error,
    })


@router.get("/masters/{entity}/new", response_class=HTMLResponse)
def masters_new(request: Request, entity: str):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    defaults = {f["key"]: f.get("default", "") for f in cfg["fields"]}
    return _render_form(request, entity, cfg, defaults, "new")


@router.post("/masters/{entity}/new")
async def masters_create(request: Request, entity: str):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    form = await request.form()
    data = {}
    for f in cfg["fields"]:
        v = form.get(f["key"])
        if f.get("type") == "password":
            if v:
                data[f["key"]] = hash_password(v)
            continue
        data[f["key"]] = coerce_field(f, v)
    try:
        cols = ",".join(data.keys())
        ph = ",".join(["?"] * len(data))
        with get_conn() as conn:
            conn.execute(f"INSERT INTO {cfg['table']} ({cols}) VALUES ({ph})",
                         tuple(data.values()))
            conn.commit()
        return RedirectResponse(f"/masters/{entity}?msg=Created", status_code=303)
    except sqlite3.IntegrityError as e:
        return _render_form(request, entity, cfg, dict(form), "new", f"Error: {e}")


@router.get("/masters/{entity}/{row_id}", response_class=HTMLResponse)
def masters_view(request: Request, entity: str, row_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    row = query_one(f"SELECT * FROM {cfg['table']} WHERE id = ?", (row_id,))
    if not row:
        raise HTTPException(404)
    return templates.TemplateResponse("masters/view.html", {
        "request": request, "user": request.cookies.get("session_user"),
        "entity": entity, "cfg": cfg, "row": row_to_dict(row),
        "msg": request.query_params.get("msg", ""),
    })


@router.get("/masters/{entity}/{row_id}/edit", response_class=HTMLResponse)
def masters_edit(request: Request, entity: str, row_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    row = query_one(f"SELECT * FROM {cfg['table']} WHERE id = ?", (row_id,))
    if not row:
        raise HTTPException(404)
    return _render_form(request, entity, cfg, row_to_dict(row), "edit")


@router.post("/masters/{entity}/{row_id}/edit")
async def masters_update(request: Request, entity: str, row_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    form = await request.form()
    data = {}
    for f in cfg["fields"]:
        v = form.get(f["key"])
        if f.get("type") == "password":
            if v:
                data[f["key"]] = hash_password(v)
            continue
        data[f["key"]] = coerce_field(f, v)
    try:
        sets = ",".join([f"{k} = ?" for k in data])
        with get_conn() as conn:
            conn.execute(f"UPDATE {cfg['table']} SET {sets} WHERE id = ?",
                         tuple(data.values()) + (row_id,))
            conn.commit()
        return RedirectResponse(f"/masters/{entity}/{row_id}?msg=Updated", status_code=303)
    except sqlite3.IntegrityError as e:
        return _render_form(request, entity, cfg, dict(form), "edit", f"Error: {e}")


@router.post("/masters/{entity}/{row_id}/delete")
def masters_delete(request: Request, entity: str, row_id: int):
    if not require_session(request):
        return RedirectResponse("/login", status_code=303)
    if entity not in MASTERS:
        raise HTTPException(404)
    cfg = MASTERS[entity]
    field_keys = [f["key"] for f in cfg["fields"]]
    if "active" in field_keys:
        with get_conn() as conn:
            conn.execute(f"UPDATE {cfg['table']} SET active = 0 WHERE id = ?", (row_id,))
            conn.commit()
        return RedirectResponse(f"/masters/{entity}?msg=Deactivated", status_code=303)
    try:
        with get_conn() as conn:
            conn.execute(f"DELETE FROM {cfg['table']} WHERE id = ?", (row_id,))
            conn.commit()
        return RedirectResponse(f"/masters/{entity}?msg=Deleted", status_code=303)
    except sqlite3.IntegrityError:
        return RedirectResponse(
            f"/masters/{entity}?error=Cannot+delete+-+referenced+by+other+records",
            status_code=303)
