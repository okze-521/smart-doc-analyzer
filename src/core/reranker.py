"""BGE Reranker — Cross-Encoder 精排

用法：
    reranker = Reranker("/app/models/bge-reranker-v2-m3")
    ranked = reranker.rerank("什么是 Qdrant？", chunks, top_k=3)
"""

import logging
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class Reranker:
    """BGE-Reranker-v2-m3 Cross-Encoder"""

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"加载 Reranker: {self.model_path}")
            self._model = CrossEncoder(self.model_path)
            logger.info("Reranker 就绪")
        return self._model

    def rerank(self, query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
        """
        对检索结果重排序

        chunks: [{"text": "...", "source_file": "...", "score": 0.6, ...}, ...]
        返回: 按 rerank 分数降序的前 top_k 个
        """
        if not chunks:
            return []

        pairs = [[query, c["text"]] for c in chunks]
        scores = self.model.predict(pairs)
        # float32 → float
        scores = [float(s) for s in scores]

        # 按分数降序
        for i, c in enumerate(chunks):
            c["rerank_score"] = scores[i]
        ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)

        return ranked[:top_k]
