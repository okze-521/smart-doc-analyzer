"""入库服务 — 文档上传 → 解析 → 切片 → 向量化 → Qdrant"""

import hashlib
from pathlib import Path

from src.core.parser import DocumentParser
from src.core.chunker import TextChunker
from src.core.embedder import TextEmbedder
from src.core.qdrant_store import QdrantStore


class IngestService:
    """文档入库流水线"""

    def __init__(
        self,
        parser: DocumentParser | None = None,
        chunker: TextChunker | None = None,
        embedder: TextEmbedder | None = None,
        qdrant: QdrantStore | None = None,
    ):
        self.parser = parser or DocumentParser()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or TextEmbedder()
        self.qdrant = qdrant or QdrantStore()

    def ingest(self, file_path: Path, doc_id: int | None = None) -> dict:
        """解析一个文档并写入向量库

        Args:
            file_path: 文档临时路径
            doc_id: 数据库文档 ID，用于关联（删除时按此字段清理 Qdrant）
        """
        # 0. 确保集合存在
        self.qdrant.ensure_collection()
        doc = self.parser.parse(file_path)

        # 2. 切片
        chunks = self.chunker.split(doc.full_text)

        # 3. 向量化 + 写入 Qdrant
        chunk_records = []
        for i, chunk_text in enumerate(chunks):
            vector = self.embedder.embed(chunk_text)
            point_id = self._make_point_id(file_path, i)
            payload = {
                "text": chunk_text,
                "chunk_index": i,
                "source_file": str(file_path),
                "file_type": doc.file_type,
                "doc_id": doc_id,
            }
            self.qdrant.upsert(
                point_id=point_id,
                vector=vector,
                payload=payload,
            )
            chunk_records.append({"index": i, "text": chunk_text[:100]})

        return {
            "filename": doc.filename,
            "file_type": doc.file_type,
            "total_pages": doc.total_pages,
            "chunk_count": len(chunks),
            "chunks": chunk_records,
            "full_text": doc.full_text,
            "metadata": doc.metadata,
        }

    def _make_point_id(self, file_path: Path, chunk_index: int) -> int:
        """生成确定性的 point ID"""
        key = f"{file_path}:{chunk_index}"
        return int(hashlib.md5(key.encode()).hexdigest()[:12], 16) % (10**10)
