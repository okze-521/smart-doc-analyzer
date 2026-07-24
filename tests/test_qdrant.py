"""Qdrant 向量库集成测试"""

import pytest
from qdrant_client import QdrantClient

from src.core.qdrant_store import QdrantStore
from tests.mock_embedder import MockEmbedder


class TestQdrantStore:
    """Qdrant 向量存储 — 使用 Mock Embedder 隔离测试"""

    @pytest.fixture
    def embedder(self):
        return MockEmbedder(dim=512)

    @pytest.fixture
    def test_collection(self):
        """每个测试用独立集合"""
        import uuid
        return f"test_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def store(self, test_collection):
        """创建并返回 store，测试后清理"""
        store = QdrantStore(collection_name=test_collection)
        store.ensure_collection(vector_size=512)
        yield store
        # 清理
        client = QdrantClient(host="localhost", port=6333)
        try:
            client.delete_collection(test_collection)
        except Exception:
            pass

    def test_collection_created(self, store):
        """集合创建成功"""
        info = store.get_collection_info()
        assert info is not None
        assert info["name"] == store.collection_name

    def test_upsert_single(self, store, embedder):
        """插入单条向量"""
        vector = embedder.embed("测试文本")
        point_id = store.upsert(
            point_id=1,
            vector=vector,
            payload={"text": "测试文本", "source": "test.pdf"}
        )
        assert point_id == 1

    def test_upsert_batch(self, store, embedder):
        """批量插入"""
        texts = ["文本1", "文本2", "文本3"]
        vectors = embedder.embed_batch(texts)
        items = [
            {
                "point_id": i + 1,
                "vector": vectors[i],
                "payload": {"text": texts[i]}
            }
            for i in range(3)
        ]
        ids = store.upsert_batch(items)
        assert len(ids) == 3

    def test_search_returns_results(self, store, embedder):
        """向量检索返回结果"""
        texts = ["Python编程", "机器学习", "天气预报"]
        vectors = embedder.embed_batch(texts)
        items = [
            {"point_id": i + 1, "vector": vectors[i], "payload": {"text": texts[i]}}
            for i in range(3)
        ]
        store.upsert_batch(items)

        # 用同一条文本检索，应该能找到自己
        query_vec = embedder.embed("Python编程")
        results = store.search(query_vec, top_k=3)
        assert len(results) >= 1
        # 同文本相同 hash → 完全相同向量 → score 接近 1.0
        assert results[0]["score"] > 0.99

    def test_search_empty_collection(self, store, embedder):
        """空集合检索返回空"""
        query_vec = embedder.embed("随便搜")
        results = store.search(query_vec, top_k=3)
        assert results == []

    def test_delete_points(self, store, embedder):
        """删除向量点"""
        vector = embedder.embed("待删除文本")
        store.upsert(999, vector, {"text": "待删除"})
        store.delete_points([999])

        # 验证已删除
        query_vec = embedder.embed("待删除")
        results = store.search(query_vec, top_k=1)
        found = [r for r in results if r["id"] == 999]
        assert len(found) == 0
