import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "mini_erp.db")
ATTACHMENTS_DIR = BASE_DIR / os.getenv("ATTACHMENTS_DIR", "data/attachments")
BACKUPS_DIR = BASE_DIR / os.getenv("BACKUPS_DIR", "data/backups")

APP_NAME = os.getenv("APP_NAME", "Mini ERP")
APP_ENV = os.getenv("APP_ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
