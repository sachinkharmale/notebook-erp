"""
Initialize the SQLite database with the complete schema + seed data.
22 SQL files, safe to re-run. Uses utf-8-sig to strip Windows BOM.
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "mini_erp.db"
SQL_DIR = ROOT / "sql"

FILES = [
    # Schema — run in dependency order
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
    # Seed — masters first, then transactions
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
    print("\nVerification:")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    print(f"  Tables ({len(tables)}):")
    for (t,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"    - {t:<25} ({count} rows)")

    views = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
    ).fetchall()
    print(f"  Views ({len(views)}):")
    for (v,) in views:
        print(f"    - {v}")

    triggers = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name"
    ).fetchall()
    print(f"  Triggers ({len(triggers)}):")
    for (t,) in triggers:
        print(f"    - {t}")

def main():
    if DB_PATH.exists():
        ans = input(f"Database {DB_PATH.name} exists. Overwrite? [y/N] ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return
        DB_PATH.unlink()

    print(f"\nCreating {DB_PATH.name}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        for fname in FILES:
            path = SQL_DIR / fname
            if not path.exists():
                print(f"  ! Missing {fname}, skipping")
                continue
            run_sql_file(conn, path)
        conn.commit()
        verify(conn)
        print(f"\nDatabase ready: {DB_PATH}")
        print(f"Size: {DB_PATH.stat().st_size:,} bytes")
    except Exception as e:
        conn.rollback()
        print(f"\nFailed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
