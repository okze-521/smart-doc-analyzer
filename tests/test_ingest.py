"""集成测试 — 文档解析 → 切片 → 向量化 → 入库 → 检索"""

import pytest
from src.core.parser import DocumentParser
from src.core.chunker import TextChunker
from src.core.qdrant_store import QdrantStore
from src.repositories.document import DocumentRepository
from tests.mock_embedder import MockEmbedder
from qdrant_client import QdrantClient


class TestIngestPipeline:
    """入库流水线：解析→切片→向量化→写入 Qdrant"""

    @pytest.fixture
    def embedder(self):
        return MockEmbedder(dim=512)

    @pytest.fixture
    def chunker(self):
        return TextChunker(chunk_size=200, overlap=30)

    @pytest.fixture
    def parser(self):
        return DocumentParser()

    @pytest.fixture
    def test_collection(self):
        import uuid
        return f"ingest_test_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def qdrant(self, test_collection):
        store = QdrantStore(collection_name=test_collection)
        store.ensure_collection(vector_size=512)
        yield store
        client = QdrantClient(host="localhost", port=6333)
        try:
            client.delete_collection(test_collection)
        except Exception:
            pass

    def test_pdf_ingest_flow(self, parser, chunker, embedder, qdrant, sample_pdf):
        """PDF → 解析 → 切片 → 向量化 → 写入 Qdrant"""
        import hashlib, time

        # 1. 解析
        parsed = parser.parse(sample_pdf)
        assert parsed.file_type == "pdf"
        assert len(parsed.sections) > 0

        # 2. 切片
        chunks = chunker.split(parsed.full_text)
        assert len(chunks) > 0

        # 3. 向量化 + 写入 Qdrant
        point_ids = []
        for i, chunk in enumerate(chunks):
            vec = embedder.embed(chunk)
            doc_id = int(hashlib.md5(f"{sample_pdf}:{i}".encode()).hexdigest()[:12], 16) % (10**10)
            qdrant.upsert(
                point_id=doc_id,
                vector=vec,
                payload={
                    "text": chunk,
                    "chunk_index": i,
                    "source_file": sample_pdf,
                    "file_type": "pdf",
                },
            )
            point_ids.append(doc_id)

        # 4. 检索验证
        query_vec = embedder.embed(chunks[0])  # 用第一个切片检索
        results = qdrant.search(query_vec, top_k=3)
        assert len(results) >= 1
        # 同文本 → 同 hash → 余弦相似度 ≈ 1.0
        assert results[0]["score"] > 0.99

    def test_docx_ingest_flow(self, parser, chunker, embedder, qdrant, sample_docx):
        """DOCX → 解析 → 切片 → 向量化 → 写入 Qdrant"""
        import hashlib

        parsed = parser.parse(sample_docx)
        assert parsed.file_type == "docx"

        chunks = chunker.split(parsed.full_text)
        assert len(chunks) > 0

        for i, chunk in enumerate(chunks):
            vec = embedder.embed(chunk)
            doc_id = int(hashlib.md5(f"docx:{i}".encode()).hexdigest()[:12], 16) % (10**10)
            qdrant.upsert(doc_id, vec, {"text": chunk, "chunk_index": i})

        info = qdrant.get_collection_info()
        assert info["points_count"] >= len(chunks)

    def test_xlsx_ingest_flow(self, parser, chunker, embedder, qdrant, sample_xlsx):
        """XLSX → 解析 → 切片 → 写入 Qdrant"""
        import hashlib

        parsed = parser.parse(sample_xlsx)
        assert parsed.file_type == "xlsx"

        chunks = chunker.split(parsed.full_text)
        assert len(chunks) > 0

        for i, chunk in enumerate(chunks):
            vec = embedder.embed(chunk)
            doc_id = int(hashlib.md5(f"xlsx:{i}".encode()).hexdigest()[:12], 16) % (10**10)
            qdrant.upsert(doc_id, vec, {"text": chunk})

        info = qdrant.get_collection_info()
        assert info["points_count"] >= len(chunks)
