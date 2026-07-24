"""文档自动分类器测试"""

import pytest
import numpy as np


class MockEmbedder:
    """mock embedder — 按关键词返回预设向量"""
    dim = 4

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        if "合同" in text:
            vec[0] = 1.0
        if "财务" in text or "收入" in text:
            vec[1] = 1.0
        if "技术" in text or "API" in text:
            vec[2] = 1.0
        if "简历" in text:
            vec[3] = 1.0
        if not any(v > 0 for v in vec):
            vec.fill(0.5)  # 通用文档 → 均匀分布
        return vec

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        return [self.embed(t) for t in texts]


@pytest.fixture
def embedder():
    return MockEmbedder()


@pytest.fixture
def categories():
    return {
        "合同": "合同协议法律条款",
        "财务报表": "财务收入支出利润",
        "技术文档": "技术API架构代码",
        "简历": "简历求职教育背景",
        "报告": "报告分析总结趋势",
    }


class TestClassifierInit:
    def test_categories_stored(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        assert len(c.categories) == 5
        assert "合同" in c.categories

    def test_category_vectors_computed(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        assert len(c._category_vectors) == len(categories)
        assert isinstance(c._category_vectors["合同"], np.ndarray)


class TestClassifierClassify:
    def test_classify_contract(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        result = c.classify("甲方与乙方签订合同，金额500万元")
        assert result["category"] == "合同"
        assert result["confidence"] > 0.5

    def test_classify_financial(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        result = c.classify("2026年第一季度财务报告，收入增长120%")
        assert result["category"] == "财务报表"

    def test_classify_technical(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        result = c.classify("API接口文档，使用FastAPI框架搭建")
        assert result["category"] == "技术文档"

    def test_classify_all_scores_returned(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        result = c.classify("通用文本内容")
        assert "all_scores" in result
        assert len(result["all_scores"]) == len(categories)
        assert result["confidence"] >= 0

    def test_classify_empty_text(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        result = c.classify("")
        assert result["category"] in categories
        assert result["confidence"] >= 0  # 空文本置信度为 0


class TestClassifierSimilarity:
    def test_similar_texts_score_higher(self, embedder, categories):
        from src.core.classifier import DocumentClassifier
        c = DocumentClassifier(embedder, categories)
        contract_score = c.classify("合同条款")["confidence"]
        other_score = c.classify("合同条款")["all_scores"]["财务报表"]
        assert contract_score > other_score
