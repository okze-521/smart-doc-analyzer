"""认证模块测试"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from src.main import app
from src.database import get_db


def _make_real_jwt(payload: dict, secret: str = "test-secret") -> str:
    """生成真实 JWT（测试用）"""
    import jwt
    return jwt.encode(payload, secret, algorithm="HS256")


class TestAuthUtils:
    """JWT 工具函数"""

    def test_create_token(self):
        from src.core.auth import create_access_token
        token = create_access_token({"sub": "testuser"}, secret="test-secret")
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_decode_valid_token(self):
        from src.core.auth import decode_access_token
        token = _make_real_jwt({"sub": "alice"}, "test-secret")
        payload = decode_access_token(token, "test-secret")
        assert payload["sub"] == "alice"

    def test_decode_expired_token(self):
        from src.core.auth import decode_access_token
        expired = datetime.utcnow() - timedelta(hours=1)
        token = _make_real_jwt(
            {"sub": "bob", "exp": expired}, "test-secret"
        )
        with pytest.raises(Exception):
            decode_access_token(token, "test-secret")

    def test_decode_invalid_token(self):
        from src.core.auth import decode_access_token
        with pytest.raises(Exception):
            decode_access_token("not.a.valid.token", "test-secret")

    def test_password_hash_and_verify(self):
        from src.core.auth import hash_password, verify_password
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"
        assert verify_password("mysecret", hashed) is True
        assert verify_password("wrong", hashed) is False


class TestAuthAPI:
    """认证 API 集成测试"""

    @pytest.fixture
    def client(self, db_session):
        """带 mock DB 的测试客户端"""
        def override_db():
            yield db_session
        app.dependency_overrides[get_db] = override_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def test_register_and_login(self, client):
        # 注册
        resp = client.post("/api/v1/auth/register", json={
            "username": "alice",
            "password": "secret123",
            "email": "alice@test.com",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert data["username"] == "alice"

        # 登录
        resp = client.post("/api/v1/auth/login", json={
            "username": "alice",
            "password": "secret123",
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_wrong_password(self, client):
        # 先注册
        client.post("/api/v1/auth/register", json={
            "username": "bob",
            "password": "rightpass",
            "email": "bob@test.com",
        })
        # 错误密码
        resp = client.post("/api/v1/auth/login", json={
            "username": "bob",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_protected_route_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_protected_route_with_token(self, client):
        # 注册获取 token
        resp = client.post("/api/v1/auth/register", json={
            "username": "charlie",
            "password": "pass123",
            "email": "charlie@test.com",
        })
        token = resp.json()["token"]

        # 用 token 访问受保护接口
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        assert resp.json()["username"] == "charlie"

    def test_duplicate_username(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "dave",
            "password": "pass123",
            "email": "dave@test.com",
        })
        resp = client.post("/api/v1/auth/register", json={
            "username": "dave",
            "password": "pass456",
            "email": "dave2@test.com",
        })
        assert resp.status_code == 409
