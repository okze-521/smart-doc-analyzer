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
    sentence-transformers qdrant-client httpx python-jose \
    passlib bcrypt pyjwt \
    && pip install --no-cache-dir -e . 2>/dev/null || true

# 源码
COPY src/ ./src/

# 数据目录
RUN mkdir -p /app/data /app/uploads /app/models

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
