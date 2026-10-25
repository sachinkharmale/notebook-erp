from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, BASE_DIR, DB_PATH
from .db import get_conn, list_tables, list_views
from .auth import hash_password
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DB_PATH.exists():
        raise RuntimeError(
            f"Database not found at {DB_PATH}. "
            "Run: python scripts/init_db.py"
        )

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM app_user WHERE username='admin'"
        ).fetchone()
        if row and row["password_hash"] == "CHANGE_ME_ON_FIRST_RUN":
            new_hash = hash_password("admin123")
            conn.execute(
                "UPDATE app_user SET password_hash = ? WHERE id = ?",
                (new_hash, row["id"]),
            )
            conn.commit()
            print("=" * 60)
            print("  Admin password set to 'admin123'")
            print("  Change it immediately in production!")
            print("=" * 60)

    tables = list_tables()
    views = list_views()
    print(f"\n{APP_NAME} ready - {len(tables)} tables, {len(views)} views")
    print(f"DB: {DB_PATH}\n")

    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)
