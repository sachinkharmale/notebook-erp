from contextlib import asynccontextmanager
from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, BASE_DIR, DB_PATH
from .db import get_conn, list_tables, list_views
from .auth import hash_password
from .routes import router
from .modules.masters.router import router as masters_router
from .modules.sales.router import router as sales_router
from .modules.production.router import router as production_router
from .modules.reports.router import router as reports_router

SYNC_MAP = {
    "customer_po": "customer_po", "wos": "wos", "bom_template": "bom_template",
    "supplier_po": "supplier_po", "grn": "grn", "indent": "indent",
    "material_issue": "material_issue", "production_entry": "production_entry",
    "packing_entry": "packing_entry", "dispatch_entry": "dispatch_entry",
    "qc_record": "qc_record", "vehicle_visit": "vehicle_visit",
    "visitor_visit": "visitor_visit", "sales_invoice": "sales_invoice",
    "purchase_invoice": "purchase_invoice", "payment_entry": "payment_entry",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DB_PATH.exists():
        raise RuntimeError(f"DB not found at {DB_PATH}. Run scripts/init_db.py")
    today = str(date.today())
    with get_conn() as conn:
        row = conn.execute("SELECT id, password_hash FROM app_user WHERE username='admin'").fetchone()
        if row and row["password_hash"] == "CHANGE_ME_ON_FIRST_RUN":
            conn.execute("UPDATE app_user SET password_hash=? WHERE id=?",
                         (hash_password("admin123"), row["id"]))
            conn.commit()
            print("Admin password set to 'admin123'")
        for entity, table in SYNC_MAP.items():
            try:
                max_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                ns = conn.execute("SELECT next_no, last_reset FROM naming_series WHERE entity=?",
                                  (entity,)).fetchone()
                if ns:
                    target = max_count + 1
                    if ns["next_no"] < target or not ns["last_reset"]:
                        conn.execute("UPDATE naming_series SET next_no=?, last_reset=? WHERE entity=?",
                                     (target, today, entity))
            except Exception:
                pass
        conn.commit()
    print(f"{APP_NAME} - {len(list_tables())} tables, {len(list_views())} views")
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)
app.include_router(masters_router)
app.include_router(sales_router)
app.include_router(production_router)
app.include_router(reports_router)
