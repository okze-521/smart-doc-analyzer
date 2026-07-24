"""RBAC 权限 + 审计中间件测试"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.database import get_db
from src.models.user import User
from src.core.auth import hash_password


@pytest.fixture
def admin_client(db_session):
    """创建管理员用户并返回带 token 的客户端"""
    # 创建 admin 用户
    admin = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        email="admin@test.com",
        is_admin=True,
    )
    db_session.add(admin)
    db_session.commit()

    # 获取 token
    def override_db():
        yield db_session
    app.dependency_overrides[get_db] = override_db

    client = TestClient(app)
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    token = resp.json()["token"]

    yield client, token
    app.dependency_overrides.clear()


@pytest.fixture
def user_client(db_session):
    """创建普通用户并返回带 token 的客户端"""
    user = User(
        username="normal",
        hashed_password=hash_password("user123"),
        email="user@test.com",
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()

    def override_db():
        yield db_session
    app.dependency_overrides[get_db] = override_db

    client = TestClient(app)
    resp = client.post("/api/v1/auth/login", json={
        "username": "normal", "password": "user123"
    })
    token = resp.json()["token"]

    yield client, token
    app.dependency_overrides.clear()


class TestRBAC:
    """权限控制测试"""

    def test_admin_can_access(self, admin_client):
        client, token = admin_client
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"

    def test_normal_user_can_access(self, user_client):
        client, token = user_client
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "normal"

    def test_unauthorized_no_token(self):
        with TestClient(app) as client:
            resp = client.get("/api/v1/auth/me")
            assert resp.status_code == 401


class TestAuditMiddleware:
    """审计模型测试"""

    def test_audit_model_works(self, db_session):
        """审计日志可写入数据库"""
        from src.models.audit import AuditLog

        log = AuditLog(
            user_id=1,
            action="upload",
            resource_type="document",
            detail="status=200 ms=45",
        )
        db_session.add(log)
        db_session.commit()

        logs = db_session.query(AuditLog).all()
        assert len(logs) >= 1
        assert logs[0].user_id == 1
        assert logs[0].action == "upload"

    def test_audit_log_has_timestamp(self, db_session):
        """审计日志自动记录时间戳"""
        from src.models.audit import AuditLog

        log = AuditLog(
            user_id=2,
            action="delete",
            resource_type="document",
        )
        db_session.add(log)
        db_session.commit()

        assert log.created_at is not None
