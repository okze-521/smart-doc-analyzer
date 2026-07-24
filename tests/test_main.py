"""测试 FastAPI 健康检查 + 骨架"""


class TestHealthEndpoint:
    """生存探针测试"""

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "app" in data
