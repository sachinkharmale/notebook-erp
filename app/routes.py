from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .config import APP_NAME, APP_ENV, BASE_DIR, ACCESS_TOKEN_EXPIRE_MINUTES
from .db import list_tables, list_views, table_count, query
from .auth import authenticate_user, create_access_token
from .dependencies import get_current_user
from .schemas.common import LoginRequest, TokenResponse, UserInfo, HealthResponse

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    tables = list_tables()
    views = list_views()
    counts = {t: table_count(t) for t in tables}
    total_rows = sum(counts.values())
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "app_env": APP_ENV,
            "tables": tables,
            "views": views,
            "counts": counts,
            "total_rows": total_rows,
        },
    )


@router.get("/health", response_model=HealthResponse)
def health():
    try:
        tables = list_tables()
        views = list_views()
        return HealthResponse(
            status="ok", app=APP_NAME, env=APP_ENV,
            db_ok=True, tables=len(tables), views=len(views),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)},
        )


@router.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/api/auth/me", response_model=UserInfo)
def me(user: dict = Depends(get_current_user)):
    return UserInfo(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        email=user.get("email"),
    )


@router.get("/api/masters/customers")
def list_customers(user: dict = Depends(get_current_user)):
    rows = query(
        "SELECT id, code, name, gstin, mobile, active FROM customer ORDER BY id"
    )
    return [dict(r) for r in rows]
