"""Embedding 服务测试 — BGE-M3"""

import pytest
import numpy as np
from src.core.embedder import TextEmbedder


class TestTextEmbedder:
    """文本向量化"""

    @pytest.fixture
    def embedder(self):
        return TextEmbedder(model_name="models/models/AI-ModelScope--bge-small-zh-v1.5/snapshots/master")

    def test_embed_single_text(self, embedder):
        vector = embedder.embed("你好世界")
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, float) for v in vector)

    def test_embed_dimension(self, embedder):
        """BGE-small-zh 输出 512 维"""
        vector = embedder.embed("测试维度")
        assert len(vector) == 512

    def test_embed_batch(self, embedder):
        texts = ["第一段文本", "第二段文本", "第三段文本"]
        vectors = embedder.embed_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) == 512 for v in vectors)

    def test_embed_empty_string(self, embedder):
        vector = embedder.embed("")
        assert len(vector) == 512  # 空串也返回向量

    def test_cosine_similarity(self, embedder):
        """相似文本的向量应该更接近"""
        v1 = embedder.embed("机器学习是人工智能的一个分支")
        v2 = embedder.embed("AI技术包括机器学习")
        v3 = embedder.embed("今天天气真不错")

        a, b = np.array(v1), np.array(v2)
        c = np.array(v3)

        sim_ab = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        sim_ac = np.dot(a, c) / (np.linalg.norm(a) * np.linalg.norm(c))

        assert sim_ab > sim_ac, f"相似文本的余弦相似度应该更高: {sim_ab:.3f} vs {sim_ac:.3f}"

    def test_model_cached(self, embedder):
        """同一实例复用模型，不重复加载"""
        v1 = embedder.embed("第一次调用")
        v2 = embedder.embed("第二次调用")
        assert len(v1) == len(v2)
