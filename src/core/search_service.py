"""Search service: embed -> retrieve -> rerank."""

from src.core.embedder import TextEmbedder
from src.core.qdrant_store import QdrantStore
from src.core.reranker import Reranker


class SearchService:
    def __init__(
        self,
        embedder: TextEmbedder | None = None,
        qdrant: QdrantStore | None = None,
        reranker: Reranker | None = None,
    ):
        self.embedder = embedder or TextEmbedder()
        self.qdrant = qdrant or QdrantStore()
        self.reranker = reranker

    def search(self, query: str, top_k: int = 5, use_reranker: bool = True) -> dict:
        """Retrieve relevant chunks, optionally rerank with cross-encoder."""
        self.qdrant.ensure_collection()

        query_vector = self.embedder.embed(query)

        # Reranker mode: fetch more candidates
        fetch_k = min(top_k * 3, 30) if (use_reranker and self.reranker) else top_k
        results = self.qdrant.search(query_vector, top_k=fetch_k)

        chunks = [
            {
                "chunk_index": r["payload"].get("chunk_index", 0),
                "text": r["payload"].get("text", ""),
                "score": round(r["score"], 4),
                "source_file": r["payload"].get("source_file", ""),
            }
            for r in results
        ]

        if use_reranker and self.reranker and chunks:
            chunks = self.reranker.rerank(query, chunks, top_k=top_k)
            for c in chunks:
                c["score"] = round(c.pop("rerank_score", c["score"]), 4)

        return {
            "query": query,
            "total_hits": len(chunks),
            "chunks": chunks,
        }
