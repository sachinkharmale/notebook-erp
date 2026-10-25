from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    email: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    db_ok: bool
    tables: int
    views: int
