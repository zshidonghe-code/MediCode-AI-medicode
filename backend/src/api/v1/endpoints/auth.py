import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError as JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from src.config.settings import get_settings

router = APIRouter()
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Simple in-memory rate limiter for login endpoint (async-safe via lock)
_login_attempts: dict[str, list[float]] = defaultdict(list)
_login_lock = asyncio.Lock()
_LOGIN_RATE_LIMIT = 50  # max attempts (generous for test suites)
_LOGIN_RATE_WINDOW = 60  # seconds

def _load_demo_users() -> dict:
    return {
        "admin": {
            "username": "admin",
            "password_hash": pwd_context.hash(settings.demo_admin_password),
            "role": "admin",
            "name": "管理员",
        },
        "coder": {
            "username": "coder",
            "password_hash": pwd_context.hash(settings.demo_coder_password),
            "role": "coder",
            "name": "编码员",
        },
        "doctor": {
            "username": "doctor",
            "password_hash": pwd_context.hash(settings.demo_doctor_password),
            "role": "doctor",
            "name": "医生",
        },
    }

DEMO_USERS = _load_demo_users()


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({
        "exp": expire,
        "iss": "medicode",
        "aud": "medicode-api",
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], audience="medicode-api", issuer="medicode")
        username = payload.get("sub")
        if username is None or username not in DEMO_USERS:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
        return DEMO_USERS[username]
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")


def require_admin(user: dict = Depends(get_current_user)):
    """管理员权限依赖项——只有 role=admin 的用户才能通过"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    name: str


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # Rate limiting by client IP (async-safe)
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    async with _login_lock:
        _login_attempts[client_ip] = [t for t in _login_attempts[client_ip] if now - t < _LOGIN_RATE_WINDOW]
        if len(_login_attempts[client_ip]) >= _LOGIN_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="登录尝试过多，请稍后再试")
        _login_attempts[client_ip].append(now)

    user = DEMO_USERS.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(
        access_token=create_token({"sub": user["username"]}),
        username=user["username"],
        role=user["role"],
        name=user["name"],
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "role": user["role"], "name": user["name"]}
