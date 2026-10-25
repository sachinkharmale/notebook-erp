"""
Initialize the SQLite database with schema + seed data.
Safe to re-run. Uses utf-8-sig to strip Windows BOM.
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
    "seed-masters.sql",
    "seed-sales.sql",
    "seed-engineering.sql",
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
    print(f"  Views ({len(views)}): {[v for (v,) in views] or 'none yet'}")

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
