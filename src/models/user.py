"""用户模型"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # documents = relationship("Document", back_populates="owner")  # Pro 版启用

    def __repr__(self):
        return f"<User {self.username}>"
