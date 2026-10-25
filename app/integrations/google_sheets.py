"""Reusable Google Sheets helper."""
import os
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

ROOT = Path(__file__).resolve().parent.parent.parent
CREDS = ROOT / "credentials.json"
SHEET_ID = os.getenv("SHEET_ID", "")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def push_rows(tab_name: str, rows: list[dict], headers: list[str] | None = None):
    """Append rows to a Google Sheet tab. Rows are dicts."""
    if not HAS_GSPREAD:
        return {"ok": False, "error": "gspread not installed"}
    if not CREDS.exists():
        return {"ok": False, "error": f"Missing {CREDS}"}
    if not SHEET_ID:
        return {"ok": False, "error": "SHEET_ID not set"}
    try:
        creds = Credentials.from_service_account_file(str(CREDS), scopes=SCOPES)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers or []) + 2)
            if headers:
                ws.append_row(headers)
        if rows:
            keys = headers or list(rows[0].keys())
            data = [[r.get(k, "") for k in keys] for r in rows]
            ws.append_rows(data, value_input_option="USER_ENTERED")
        return {"ok": True, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
