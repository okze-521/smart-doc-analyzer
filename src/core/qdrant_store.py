"""Qdrant 向量存储 — 封装客户端操作"""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config import settings


class QdrantStore:
    """Qdrant 向量库读写封装"""

    def __init__(self, collection_name: str | None = None):
        self._client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = collection_name or settings.QDRANT_COLLECTION

    # ----------------------------------------------------------------
    #  集合管理
    # ----------------------------------------------------------------

    def ensure_collection(self, vector_size: int | None = None) -> None:
        """创建集合（幂等）"""
        vs = vector_size or settings.EMBEDDING_DIM
        try:
            self._client.get_collection(self.collection_name)
        except (UnexpectedResponse, Exception):
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vs, distance=Distance.COSINE),
            )

    def get_collection_info(self) -> dict | None:
        """获取集合信息"""
        try:
            info = self._client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": getattr(info, "points_count", 0),
                "vectors_count": getattr(info, "vectors_count", info.points_count),
            }
        except Exception:
            return None

    # ----------------------------------------------------------------
    #  写入
    # ----------------------------------------------------------------

    def upsert(self, point_id: str, vector: list[float], payload: dict) -> str:
        """插入/更新单条向量"""
        self._client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(id=point_id, vector=vector, payload=payload)
            ],
            wait=True,
        )
        return point_id

    def upsert_batch(self, items: list[dict]) -> list[str]:
        """
        批量插入。
        items: [{"point_id": str, "vector": list[float], "payload": dict}, ...]
        """
        points = [
            PointStruct(id=item["point_id"], vector=item["vector"], payload=item["payload"])
            for item in items
        ]
        self._client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        return [item["point_id"] for item in items]

    # ----------------------------------------------------------------
    #  检索
    # ----------------------------------------------------------------

    def search(self, query_vector: list[float], top_k: int = 10) -> list[dict]:
        """余弦相似度检索"""
        results = self._client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results.points
        ]

    # ----------------------------------------------------------------
    #  删除
    # ----------------------------------------------------------------

    def delete_points(self, point_ids: list[str]) -> None:
        """按 ID 删除向量点"""
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids,
            wait=True,
        )
