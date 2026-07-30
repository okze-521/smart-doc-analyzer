"""认证 API（注册、登录、用户信息）"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.models.user import User
from src.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: str = Field(..., max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


# ── 注册 ────────────────────────────────────

@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(409, "用户名已存在")

    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        email=req.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        {"sub": user.username},
        settings.SECRET_KEY,
    )
    return {"token": token, "username": user.username}


# ── 登录 ────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "用户名或密码错误")

    token = create_access_token(
        {"sub": user.username},
        settings.SECRET_KEY,
    )
    return {"token": token, "username": user.username}


# ── 当前用户 ────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从 Bearer token 解析当前用户"""
    try:
        payload = decode_access_token(credentials.credentials, settings.SECRET_KEY)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(401, "无效 token")
    except Exception:
        raise HTTPException(401, "token 无效或已过期")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
    }
