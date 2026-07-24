"""数据库引擎 + 会话工厂"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.config import settings

# SQLite 需要 check_same_thread=False（FastAPI 多线程下兼容）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,  # DEBUG 模式下打印 SQL
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """ORM 基类 — 所有模型继承它"""
    pass


def get_db():
    """FastAPI 依赖注入：每个请求获取独立 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
