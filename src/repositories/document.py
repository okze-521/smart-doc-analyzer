"""Document Repository — 文档元数据 CRUD"""
from datetime import datetime

from sqlalchemy.orm import Session

from src.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- 创建 ----

    def create(
        self,
        filename: str,
        original_filename: str,
        file_type: str,
        file_size: int = 0,
        page_count: int = 0,
        metadata_json: dict | None = None,
        owner_id: int | None = None,
    ) -> Document:
        doc = Document(
            filename=filename,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            page_count=page_count,
            metadata_json=metadata_json or {},
            status="uploaded",
            owner_id=owner_id,
        )
        self.session.add(doc)
        self.session.commit()
        self.session.refresh(doc)
        return doc

    # ---- 查询 ----

    def get_by_id(self, doc_id: int) -> Document | None:
        return self.session.get(Document, doc_id)

    def list_all(self, offset: int = 0, limit: int = 20) -> list[Document]:
        return (
            self.session.query(Document)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    # ---- 更新 ----

    def update_status(self, doc_id: int, status: str) -> Document | None:
        doc = self.get_by_id(doc_id)
        if doc is None:
            return None
        doc.status = status
        self.session.commit()
        self.session.refresh(doc)
        return doc

    def update_metadata(self, doc_id: int, metadata: dict, **kwargs) -> Document | None:
        doc = self.get_by_id(doc_id)
        if doc is None:
            return None
        doc.metadata_json = {**doc.metadata_json, **metadata}
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        self.session.commit()
        self.session.refresh(doc)
        return doc

    # ---- 删除 ----

    def delete(self, doc_id: int) -> bool:
        doc = self.get_by_id(doc_id)
        if doc is None:
            return False
        self.session.delete(doc)
        self.session.commit()
        return True
