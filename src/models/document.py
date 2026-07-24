"""文档元数据模型"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from src.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)           # 存储文件名 (uuid.pdf)
    original_filename = Column(String(255), nullable=False)   # 原始文件名
    file_type = Column(String(10), nullable=False)            # pdf / docx / xlsx
    file_size = Column(Integer, default=0)                    # 字节
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)                # 提取的元数据 {author, title, ...}
    status = Column(String(20), default="uploaded")           # uploaded → processing → ready / error
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.original_filename}>"
