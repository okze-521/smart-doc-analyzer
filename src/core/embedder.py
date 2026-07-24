"""文本向量化 — sentence-transformers 封装"""

import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import settings


class TextEmbedder:
    """文本 → 固定维度向量（默认 BGE-M3, 1024 维）"""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._model: SentenceTransformer | None = None

    # ----------------------------------------------------------------
    #  延迟加载（避免测试环境空跑下载）
    # ----------------------------------------------------------------

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self._model_name,
                device="cpu",
            )
        return self._model

    @property
    def dim(self) -> int:
        """向量维度"""
        return self.model.get_sentence_embedding_dimension()

    # ----------------------------------------------------------------
    #  接口
    # ----------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        """单条文本 → 向量"""
        vec = self.model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量文本 → 向量列表"""
        vecs = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vecs]

    def similarity(self, v1: list[float], v2: list[float]) -> float:
        """两个向量的余弦相似度 [-1, 1]"""
        a, b = np.array(v1), np.array(v2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
