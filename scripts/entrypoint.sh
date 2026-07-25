#!/bin/bash
set -e

echo "🔧 Smart Doc Analyzer — 启动中..."

# 自动建表
python -c "
from src.database import engine, Base
from src.models import User, Document, AuditLog
Base.metadata.create_all(bind=engine)
print('✅ 数据库表已就绪 (users, documents, audit_logs)')
"

echo "🚀 启动 FastAPI..."
exec "$@"
