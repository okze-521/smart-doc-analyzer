"""审计日志模型"""

import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=False)        # search / upload / delete / download
    resource_type = Column(String(50), nullable=True)   # document / search
    resource_id = Column(Integer, nullable=True)
    detail = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __repr__(self):
        return f"<AuditLog {self.action} by user#{self.user_id}>"
