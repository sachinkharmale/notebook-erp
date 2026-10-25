from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.hash import pbkdf2_sha256
from .config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from .db import query_one

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pbkdf2_sha256.verify(password, hashed)
    except Exception:
        return False


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    minutes = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def authenticate_user(username: str, password: str):
    row = query_one(
        "SELECT * FROM app_user WHERE username = ? AND active = 1", (username,)
    )
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return dict(row)
