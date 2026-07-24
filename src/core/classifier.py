"""文档自动分类器 — 基于 BGE 向量相似度"""

from typing import Any
import numpy as np


class DocumentClassifier:
    """通过文本嵌入与类别描述向量的余弦相似度进行分类"""

    def __init__(self, embedder: Any, categories: dict[str, str]):
        self.embedder = embedder
        self.categories = categories  # {"合同": "描述文字", ...}
        self._category_vectors: dict[str, np.ndarray] = {}
        self._compute_category_vectors()

    # ── 分类主逻辑 ────────────────────────────

    def classify(self, text: str) -> dict:
        """对文本分类，返回 {category, confidence, all_scores}"""
        if not text.strip():
            # 空文本 → 返回第一个类别，0 置信度
            first_cat = list(self.categories.keys())[0]
            return {
                "category": first_cat,
                "confidence": 0.0,
                "all_scores": {k: 0.0 for k in self.categories},
            }

        text_vec = self.embedder.embed(text)

        # 计算与每个类别的余弦相似度
        scores: dict[str, float] = {}
        for name, cat_vec in self._category_vectors.items():
            scores[name] = self._cosine_similarity(text_vec, cat_vec)

        best_category = max(scores, key=scores.__getitem__)
        return {
            "category": best_category,
            "confidence": round(float(scores[best_category]), 4),
            "all_scores": {k: round(float(v), 4) for k, v in scores.items()},
        }

    # ── 内部方法 ───────────────────────────────

    def _compute_category_vectors(self):
        """预计算所有类别的向量"""
        for name, description in self.categories.items():
            self._category_vectors[name] = self.embedder.embed(description)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
