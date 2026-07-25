# Smart Doc Analyzer — FastAPI 应用镜像
FROM python:3.11-slim

WORKDIR /app

# 系统依赖（PDF 解析需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（先装依赖利用 Docker 缓存层）
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] sqlalchemy pydantic-settings \
    python-multipart aiofiles pymupdf python-docx openpyxl \
    "sentence-transformers>=3.0" "qdrant-client>=1.9,<1.12" httpx python-jose \
    passlib bcrypt pyjwt

# 源码、前端页面、启动脚本
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY chat.html .
RUN chmod +x /app/scripts/entrypoint.sh
 
# 数据目录
RUN mkdir -p /app/data /app/uploads /app/models
 
EXPOSE 8000
 
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
