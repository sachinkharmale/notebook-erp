"""SQLite connection helpers — no ORM, no server, just files."""
import sqlite3
from pathlib import Path
from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()):
    with get_conn() as conn:
        return conn.execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def list_tables() -> list[str]:
    rows = query(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [r["name"] for r in rows]


def list_views() -> list[str]:
    rows = query("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
    return [r["name"] for r in rows]
