"""文档元数据模型"""

import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

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
    content = Column(Text, default="")                        # 解析后的全文，供对比/分类等分析使用
    status = Column(String(20), default="uploaded")           # uploaded → processing → ready / error
    owner_id = Column(Integer, nullable=True)  # Pro 版启用 FK 到 users.id
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # owner = relationship("User", back_populates="documents")  # Pro 版启用

    def __repr__(self):
        return f"<Document {self.original_filename}>"
