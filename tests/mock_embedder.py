"""Mock Embedder — 单元测试用，不依赖模型下载"""
import hashlib


class MockEmbedder:
    """确定性伪向量（基于文本 hash），用于隔离测试"""

    def __init__(self, dim: int = 512):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        # 用 hash 生成确定性向量
        vec = []
        for i in range(self.dim):
            byte_idx = i % len(h)
            vec.append((h[byte_idx] / 255.0) * 2 - 1)
        # 归一化
        norm = sum(v ** 2 for v in vec) ** 0.5
        return [v / norm for v in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
