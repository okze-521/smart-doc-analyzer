"""文档对比 API 集成测试"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.core.comparator import Comparator
from src.core.llm_client import LLMClient


@pytest.fixture
def mock_llm():
    """mock LLM，返回固定摘要"""
    m = AsyncMock()
    m.generate = AsyncMock(return_value="对比摘要：金额从500万变更为650万，新增第二章。")
    return m


@pytest.fixture
def client(mock_llm):
    """注入 mock comparator 的测试客户端"""
    def override_comparator():
        llm = LLMClient(provider="deepseek", deepseek_api_key="test")
        llm.generate = mock_llm.generate
        return Comparator(llm_client=llm)

    from src.api.analysis import get_comparator
    app.dependency_overrides[get_comparator] = override_comparator

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestCompareAPI:
    def test_compare_texts(self, client, mock_llm):
        """通过 text_1/text_2 对比"""
        resp = client.post("/api/v1/analysis/compare", json={
            "text_1": "合同金额500万",
            "text_2": "合同金额650万\n新增条款：违约金10%",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["identical"] is False
        assert data["line_changes"] > 0
        assert data["summary"] is not None
        assert "500万" in data["summary"] or "650万" in data["summary"]

    def test_compare_identical(self, client):
        """相同文本对比"""
        resp = client.post("/api/v1/analysis/compare", json={
            "text_1": "相同的文本",
            "text_2": "相同的文本",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["identical"] is True
        assert data["line_changes"] == 0

    def test_compare_empty_body(self, client):
        """空请求体应 400"""
        resp = client.post("/api/v1/analysis/compare", json={})
        assert resp.status_code == 400 or resp.status_code == 422

    def test_compare_missing_both_sides(self, client):
        """只传一边应 400"""
        resp = client.post("/api/v1/analysis/compare", json={
            "text_1": "只有这边",
        })
        assert resp.status_code in (400, 422)

    def test_compare_missing_doc(self, client):
        """doc_id 不存在应 404"""
        resp = client.post("/api/v1/analysis/compare", json={
            "doc_id_1": 99999,
            "doc_id_2": 99998,
        })
        assert resp.status_code == 404
