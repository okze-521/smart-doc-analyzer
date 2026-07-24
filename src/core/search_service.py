"""检索服务 — 查询向量化 → Qdrant 检索"""

from src.core.embedder import TextEmbedder
from src.core.qdrant_store import QdrantStore


class SearchService:
    def __init__(
        self,
        embedder: TextEmbedder | None = None,
        qdrant: QdrantStore | None = None,
    ):
        self.embedder = embedder or TextEmbedder()
        self.qdrant = qdrant or QdrantStore()

    def search(self, query: str, top_k: int = 5) -> dict:
        """检索相关文档片段"""
        # 1. 向量化
        query_vector = self.embedder.embed(query)

        # 2. 检索
        results = self.qdrant.search(query_vector, top_k=top_k)

        # 3. 格式化
        chunks = [
            {
                "chunk_index": r["payload"].get("chunk_index", 0),
                "text": r["payload"].get("text", ""),
                "score": round(r["score"], 4),
                "source_file": r["payload"].get("source_file", ""),
            }
            for r in results
        ]

        return {
            "query": query,
            "total_hits": len(chunks),
            "chunks": chunks,
        }
