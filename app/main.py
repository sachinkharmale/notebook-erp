from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, BASE_DIR, DB_PATH
from .db import get_conn, list_tables, list_views
from .auth import hash_password
from .routes import router
from .modules.masters.router import router as masters_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found at {DB_PATH}. Run: python scripts/init_db.py")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM app_user WHERE username='admin'"
        ).fetchone()
        if row and row["password_hash"] == "CHANGE_ME_ON_FIRST_RUN":
            conn.execute("UPDATE app_user SET password_hash = ? WHERE id = ?",
                         (hash_password("admin123"), row["id"]))
            conn.commit()
            print("=" * 60)
            print("  Admin password set to 'admin123'")
            print("=" * 60)
    print(f"\n{APP_NAME} ready - {len(list_tables())} tables, {len(list_views())} views")
    print(f"DB: {DB_PATH}\n")
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)
app.include_router(masters_router)
