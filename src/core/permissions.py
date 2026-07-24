"""权限控制 — 基于用户角色的路由保护"""

from functools import wraps

from fastapi import HTTPException, Depends
from src.models.user import User
from src.api.auth import get_current_user


def require_role(role: str):
    """依赖注入：要求用户具备某角色（如 'admin'）"""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if role == "admin" and not user.is_admin:
            raise HTTPException(403, "需要管理员权限")
        # 未来可扩展更多角色
        return user
    return role_checker
