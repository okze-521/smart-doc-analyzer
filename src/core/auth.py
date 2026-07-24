"""JWT 认证工具"""

from datetime import datetime, timedelta
import jwt
import bcrypt


# ── 密码 ────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ─────────────────────────────────────

def create_access_token(
    data: dict,
    secret: str,
    expires_delta: timedelta = timedelta(hours=24),
) -> str:
    """生成 JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> dict:
    """解码并验证 JWT token"""
    return jwt.decode(token, secret, algorithms=["HS256"])
