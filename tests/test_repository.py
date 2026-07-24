"""Document Repository 测试"""

import pytest
from datetime import datetime

from src.repositories.document import DocumentRepository
from src.models.document import Document


class TestDocumentRepository:
    """文档元数据 CRUD"""

    @pytest.fixture
    def repo(self, db_session):
        return DocumentRepository(db_session)

    def test_create_document(self, repo):
        doc = repo.create(
            filename="test_report.pdf",
            original_filename="年报2024.pdf",
            file_type="pdf",
            file_size=102400,
            page_count=12,
        )
        assert doc.id is not None
        assert doc.filename == "test_report.pdf"
        assert doc.status == "uploaded"
        # 自动设置时间戳
        assert doc.created_at is not None

    def test_get_by_id(self, repo):
        doc = repo.create(
            filename="get_test.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size=100,
            page_count=1,
        )
        fetched = repo.get_by_id(doc.id)
        assert fetched is not None
        assert fetched.filename == "get_test.pdf"

    def test_get_not_found(self, repo):
        doc = repo.get_by_id(99999)
        assert doc is None

    def test_list_documents(self, repo):
        # 创建 3 个文档
        for i in range(3):
            repo.create(
                filename=f"doc_{i}.pdf",
                original_filename=f"原始_{i}.pdf",
                file_type="pdf",
                file_size=100,
                page_count=1,
            )
        docs = repo.list_all(limit=10)
        assert len(docs) == 3

    def test_update_status(self, repo):
        doc = repo.create(
            filename="status_test.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size=100,
            page_count=1,
        )
        updated = repo.update_status(doc.id, "processed")
        assert updated.status == "processed"

    def test_delete_document(self, repo):
        doc = repo.create(
            filename="delete_test.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size=100,
            page_count=1,
        )
        assert repo.delete(doc.id) is True
        assert repo.get_by_id(doc.id) is None

    def test_delete_not_found(self, repo):
        assert repo.delete(99999) is False

    def test_pagination(self, repo):
        for i in range(5):
            repo.create(
                filename=f"page_{i}.pdf",
                original_filename=f"p_{i}.pdf",
                file_type="pdf",
                file_size=100,
                page_count=1,
            )
        page1 = repo.list_all(offset=0, limit=2)
        page2 = repo.list_all(offset=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2
        # 两页不重叠
        ids1 = {d.id for d in page1}
        ids2 = {d.id for d in page2}
        assert ids1.isdisjoint(ids2)
