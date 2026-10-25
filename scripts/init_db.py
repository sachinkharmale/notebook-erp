"""
Initialize the SQLite database with complete schema + seed + MRP view.
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "mini_erp.db"
SQL_DIR = ROOT / "sql"

FILES = [
    "01-masters.sql",
    "02-sales.sql",
    "03-engineering.sql",
    "04-procurement.sql",
    "05-inventory.sql",
    "06-triggers.sql",
    "07-production.sql",
    "08-quality.sql",
    "09-production-views.sql",
    "10-production-triggers.sql",
    "11-gate.sql",
    "12-finance.sql",
    "13-crosscutting.sql",
    "14-finance-views.sql",
    "15-mrp-view.sql",
    "seed-masters.sql",
    "seed-sales.sql",
    "seed-engineering.sql",
    "seed-procurement.sql",
    "seed-production.sql",
    "seed-gate.sql",
    "seed-finance.sql",
    "seed-crosscutting.sql",
]

def run_sql_file(conn, path):
    print(f"  -> {path.name}")
    conn.executescript(path.read_text(encoding="utf-8-sig"))

def verify(conn):
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    views = conn.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name").fetchall()
    triggers = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name").fetchall()
    print(f"\n  Tables: {len(tables)}   Views: {len(views)}   Triggers: {len(triggers)}")

def main():
    if DB_PATH.exists():
        ans = input(f"Database {DB_PATH.name} exists. Overwrite? [y/N] ").strip().lower()
        if ans != "y":
            print("Aborted."); return
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        for fname in FILES:
            path = SQL_DIR / fname
            if path.exists():
                run_sql_file(conn, path)
        conn.commit()
        verify(conn)
        print(f"\nDatabase ready: {DB_PATH}")
    except Exception as e:
        conn.rollback(); print(f"\nFailed: {e}"); sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
