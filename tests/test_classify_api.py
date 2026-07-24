"""文档分类 API 集成测试"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from src.main import app
from src.core.classifier import DocumentClassifier


class MockEmbedder:
    """mock embedder"""
    dim = 4

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        if "合同" in text:
            vec[0] = 1.0
        if "财务" in text or "收入" in text:
            vec[1] = 1.0
        if "技术" in text or "API" in text:
            vec[2] = 1.0
        if "报告" in text or "调研" in text:
            vec[3] = 1.0
        if not any(v > 0 for v in vec):
            vec.fill(0.5)
        return vec

    def embed_batch(self, texts):
        return [self.embed(t) for t in texts]


MOCK_CATEGORIES = {
    "合同": "合同协议",
    "财务报表": "财务收入",
    "技术文档": "技术API",
    "报告": "报告分析",
}


@pytest.fixture
def client():
    """注入 mock classifier"""
    def override_classifier():
        return DocumentClassifier(MockEmbedder(), MOCK_CATEGORIES)

    from src.api.analysis import get_classifier
    app.dependency_overrides[get_classifier] = override_classifier

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestClassifyAPI:
    def test_classify_text(self, client):
        resp = client.post("/api/v1/analysis/classify", json={
            "text": "甲方乙方签订合同，违约赔偿条款"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "合同"
        assert data["confidence"] > 0.5
        assert "all_scores" in data

    def test_classify_financial(self, client):
        resp = client.post("/api/v1/analysis/classify", json={
            "text": "季度财务报表显示收入大幅增长"
        })
        assert resp.status_code == 200
        assert resp.json()["category"] == "财务报表"

    def test_classify_empty(self, client):
        resp = client.post("/api/v1/analysis/classify", json={
            "text": ""
        })
        assert resp.status_code == 400

    def test_classify_empty_body(self, client):
        resp = client.post("/api/v1/analysis/classify", json={})
        assert resp.status_code in (400, 422)

    def test_classify_missing_doc(self, client):
        resp = client.post("/api/v1/analysis/classify", json={
            "doc_id": 99999
        })
        assert resp.status_code == 404
