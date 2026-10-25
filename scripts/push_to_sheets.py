"""Push tables to a Google Sheet. No server needed — run manually or via Task Scheduler.

Setup (one-time):
  1. Go to https://console.cloud.google.com → create project → enable Google Sheets API
  2. Create Service Account → create JSON key → download as `credentials.json`
  3. Share your target Google Sheet with the service account email (Editor)
  4. Set SHEET_ID in .env
  5. Run: python scripts/push_to_sheets.py
"""
import os
import sys
from pathlib import Path
import sqlite3

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Install gspread: pip install gspread google-auth")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "mini_erp.db"
CREDS = ROOT / "credentials.json"
SHEET_ID = os.getenv("SHEET_ID", "")

# Tables to push — one tab per table
TABLES = [
    "customer", "supplier", "material", "sku", "warehouse", "uom",
    "customer_po", "customer_po_line", "wos",
    "bom_template", "bom_template_line", "wos_bom", "wos_bom_line",
    "supplier_po", "supplier_po_line", "grn", "grn_line",
    "stock_ledger",
    "indent", "indent_line", "material_issue", "material_issue_line",
    "production_entry", "packing_entry", "dispatch_entry",
    "qc_record", "vehicle_visit", "visitor_visit",
    "sales_invoice", "purchase_invoice", "payment_entry", "payment_allocation",
]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_client():
    if not CREDS.exists():
        print(f"Missing {CREDS}. See setup instructions in script header.")
        sys.exit(1)
    creds = Credentials.from_service_account_file(str(CREDS), scopes=SCOPES)
    return gspread.authorize(creds)


def push_table(sh, conn, table):
    try:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    except sqlite3.OperationalError:
        print(f"  {table}: skip (doesn't exist)")
        return
    if not rows:
        print(f"  {table}: 0 rows")
        return
    headers = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
    data = [headers] + [[r[i] for i in range(len(headers))] for r in rows]
    try:
        ws = sh.worksheet(table)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=table, rows=len(data) + 10, cols=len(headers) + 2)
    ws.update(range_name="A1", values=data)
    print(f"  {table}: {len(rows)} rows")


def main():
    if not SHEET_ID:
        print("Set SHEET_ID env var (or add to .env)")
        sys.exit(1)
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        sys.exit(1)
    print(f"Pushing to sheet {SHEET_ID}...")
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        for t in TABLES:
            push_table(sh, conn, t)
    finally:
        conn.close()
    print(f"\nDone. {len(TABLES)} tables pushed.")


if __name__ == "__main__":
    main()
