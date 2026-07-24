"""初始化数据库 — 创建所有表"""
import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import engine, Base
from src.models import User, Document, AuditLog  # noqa: F401 — 触发模型注册

print("正在创建数据库表...")
Base.metadata.create_all(bind=engine)
print("✅ 数据库初始化完成！")
print(f"   表: users, documents, audit_logs")
