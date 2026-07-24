# Smart Doc Analyzer — 企业文档智能分析平台

> 实施计划 v1.0 | 2026-07-24

---

## 一、项目概述

### 1.1 一句话定位

企业级文档智能分析平台——不只是"问文档"，而是解析文档结构、提取表格数据、对比版本差异、自动分类归档。

### 1.2 目标岗位

投递方向：**AI 应用工程师 / 大模型应用开发 / LLM Ops**

### 1.3 与 Personal RAG Platform 的关系

| | Personal RAG Platform | Smart Doc Analyzer |
|---|---|---|
| 定位 | RAG 技术可行性验证 | **企业级工程交付证明** |
| 用户 | 单用户（自己） | 多用户 + RBAC 权限 |
| 输入 | Markdown 文本 | PDF / Word / Excel / PPT |
| 输出 | 一段回答 | 检索 + 结构化数据 + 对比 + 分类 |
| 测试 | 无 | pytest 全覆盖 |
| 部署 | 单容器 | Docker Compose 多服务 |

**两者不是替代关系，而是维度升级：从"我会 RAG"到"我能交付企业系统"。**

---

## 二、技术架构

### 2.1 架构图

```
┌──────────────────────────────────────────────────┐
│                  前端 (可选)                       │
│            文档上传 · 检索 · 对比 · 分类            │
└────────────────────┬─────────────────────────────┘
                     │ REST API (JWT Auth)
┌────────────────────▼─────────────────────────────┐
│               FastAPI (async/await)               │
│                                                    │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ 文档解析   │  │ 语义检索   │  │ 对比/分类     │  │
│  │ PDF/DOCX  │  │+结构化过滤 │  │ + 报告生成    │  │
│  │ 表格提取   │  │           │  │              │  │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘  │
│        │              │               │          │
│  ┌─────▼──────────────▼───────────────▼───────┐   │
│  │         ARQ 异步任务队列 (Redis)            │   │
│  │  大文档解析不阻塞 API，支持进度查询          │   │
│  └────────────────────────────────────────────┘   │
└──────┬───────────────┬───────────────┬────────────┘
       │               │               │
┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
│  SQLite     │  │   Qdrant    │  │  本地文件   │
│  元数据     │  │  向量检索    │  │  存储       │
│  用户·审计   │  │  (复用现有)  │  │  uploads/   │
└─────────────┘  └─────────────┘  └────────────┘
```

### 2.2 技术选型

| 层级 | 技术 | 版本 | 为什么选它 |
|------|------|------|-----------|
| Web 框架 | FastAPI | ≥0.115 | 原生 async，AI 项目标配 |
| ORM | SQLAlchemy 2.0 | ≥2.0 | 企业项目标准，面试高频 |
| 数据库 | SQLite (开发) | — | 零配置，后期可换 PostgreSQL |
| 向量库 | Qdrant | 复用现有容器 | 已有环境，无需重装 |
| 任务队列 | ARQ | ≥0.26 | 轻量 Celery 替代，Redis 驱动 |
| Embedding | BGE-M3 | 复用笔记本 | 已有模型，1024 维 |
| LLM | qwen3.6:35b-a3b | 台式机 192.168.3.200 | 已有推理节点 |
| 文档解析 | PyPDF2 + python-docx + openpyxl | 最新 | 三大办公格式全覆盖 |
| 测试 | pytest + pytest-asyncio | ≥8.0 | TDD 从第一天开始 |
| 认证 | python-jose + passlib | 最新 | JWT 无状态认证 |
| 部署 | Docker Compose | — | 4 个服务一键启动 |

### 2.3 环境依赖

```
笔记本 (当前开发机):
  - Python 3.11+
  - Docker Desktop (Qdrant + Redis)
  - BGE-M3 模型 (本地 CPU)

台式机 192.168.3.200:
  - Ollama + qwen3.6:35b-a3b (LLM 推理)
  - 仅集成测试时需要开机
```

---

## 三、目录结构

```
smart-doc-analyzer/
├── .env                          # 环境变量（不进 Git）
├── .env.example                  # 环境变量模板（进 Git）
├── .gitignore
├── docker-compose.yml            # Qdrant + Redis + API + Worker
├── Dockerfile                    # FastAPI 镜像
├── pyproject.toml                # uv 依赖管理
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   ├── config.py                 # Pydantic Settings 配置
│   ├── database.py               # SQLAlchemy engine + session
│   │
│   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── __init__.py
│   │   ├── user.py               # 用户表
│   │   ├── document.py           # 文档元数据表
│   │   └── audit.py              # 审计日志表
│   │
│   ├── schemas/                  # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   └── search.py
│   │
│   ├── api/                      # 路由模块
│   │   ├── __init__.py
│   │   ├── auth.py               # 登录/注册/Token
│   │   ├── documents.py          # 上传/列表/删除
│   │   ├── search.py             # 语义搜索 + 过滤
│   │   └── analysis.py           # 对比/分类/报告
│   │
│   ├── core/                     # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── parser.py             # 文档解析引擎
│   │   ├── chunker.py            # 文本切片
│   │   ├── embedder.py           # BGE-M3 向量化
│   │   ├── retriever.py          # Qdrant 检索 + 元数据过滤
│   │   ├── llm_client.py         # Ollama LLM 客户端 (async httpx)
│   │   ├── comparator.py         # 文档对比
│   │   └── classifier.py         # 零样本分类
│   │
│   ├── tasks/                    # ARQ 异步任务
│   │   ├── __init__.py
│   │   └── document.py           # 文档解析任务
│   │
│   └── middleware/               # 中间件
│       ├── __init__.py
│       └── audit.py              # 审计日志中间件
│
├── tests/                        # pytest 测试
│   ├── __init__.py
│   ├── conftest.py               # fixtures: client, db, mock_llm
│   ├── test_config.py
│   ├── test_parser.py
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   ├── test_llm_client.py
│   ├── test_api_auth.py
│   ├── test_api_documents.py
│   ├── test_api_search.py
│   └── test_comparator.py
│
├── uploads/                      # 上传文件存储（不进 Git）
├── docs/
│   ├── implementation-plan.md    # 本文档
│   └── api-reference.md          # API 文档（自动生成）
│
└── scripts/
    ├── init_db.py                # 初始化数据库表
    └── seed_data.py              # 测试数据填充
```

---

## 四、分阶段实施计划

### 第一阶段：项目骨架 + 测试基础设施（Day 1-2）

#### 任务 1.1：初始化项目

**目标**：创建项目目录、配置 pyproject.toml、安装核心依赖

**文件**：
- 创建 `D:/Projects/smart-doc-analyzer/pyproject.toml`
- 创建 `D:/Projects/smart-doc-analyzer/.env.example`
- 创建 `D:/Projects/smart-doc-analyzer/.gitignore`

**依赖列表**：
```toml
[project]
name = "smart-doc-analyzer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",
    "httpx>=0.27.0",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "python-multipart>=0.0.9",
    "PyPDF2>=3.0",
    "python-docx>=1.1",
    "openpyxl>=3.1",
    "qdrant-client>=1.9",
    "sentence-transformers>=3.0",
    "arq>=0.26.0",
    "redis>=5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "httpx>=0.27.0",
]
```

**验证**：`uv pip install -e ".[dev]"` 成功无报错

---

#### 任务 1.2：配置管理

**目标**：创建 Pydantic Settings 配置类，所有敏感信息走 .env

**文件**：
- 创建 `src/__init__.py`
- 创建 `src/config.py`

**代码骨架**：
```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "Smart Doc Analyzer"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 数据库
    DATABASE_URL: str = "sqlite:///./data/smart_doc.db"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "smart_docs"

    # Ollama (台式机)
    OLLAMA_HOST: str = "http://192.168.3.200:11434"
    OLLAMA_MODEL: str = "qwen3.6:35b-a3b"

    # Embedding
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024
    HF_ENDPOINT: str = "https://hf-mirror.com"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # 切片
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # 检索
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

**验证**：`python -c "from src.config import settings; print(settings.APP_NAME)"` → 输出 "Smart Doc Analyzer"

---

#### 任务 1.3：数据库模型

**目标**：创建 SQLAlchemy ORM 模型（用户、文档、审计日志）

**文件**：
- 创建 `src/database.py`
- 创建 `src/models/__init__.py`
- 创建 `src/models/user.py`
- 创建 `src/models/document.py`
- 创建 `src/models/audit.py`

**关键模型**：

```python
# src/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    documents = relationship("Document", back_populates="owner")
```

```python
# src/models/document.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.database import Base
import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, xlsx
    file_size = Column(Integer)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    metadata_json = Column(JSON, default={})  # 提取的元数据
    status = Column(String(20), default="uploaded")  # uploaded, processing, ready, error
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="documents")
```

**验证**：`python scripts/init_db.py` → 数据库文件 `data/smart_doc.db` 生成，包含 3 张表

---

#### 任务 1.4：pytest 基础设施

**目标**：搭好测试框架，写第一个测试验证一切就绪

**文件**：
- 创建 `tests/__init__.py`
- 创建 `tests/conftest.py`
- 创建 `tests/test_config.py`

**conftest.py 核心 fixtures**：
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db

# 测试用内存数据库
TEST_DATABASE_URL = "sqlite:///./data/test.db"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    from src.main import app
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
```

**第一个测试**：
```python
# tests/test_config.py
from src.config import settings

def test_settings_load():
    assert settings.APP_NAME == "Smart Doc Analyzer"
    assert settings.EMBEDDING_DIM == 1024
    assert isinstance(settings.DEBUG, bool)
```

**验证**：`pytest tests/test_config.py -v` → 1 passed

---

### 第二阶段：文档解析引擎（Day 3-5）

#### 任务 2.1：PDF 解析器

**目标**：解析 PDF 文件，提取文本 + 表格 + 元数据

**文件**：
- 创建 `src/core/parser.py`
- 创建 `tests/test_parser.py`

**核心接口**：
```python
# src/core/parser.py
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ParsedSection:
    """解析后的文档片段"""
    section_type: str       # "heading", "paragraph", "table", "list"
    level: int = 0          # 标题级别 (h1=1, h2=2...)
    content: str = ""       # 文本内容
    table_data: list = field(default_factory=list)  # 表格数据 [[row1], [row2]]
    page_number: int = 1
    metadata: dict = field(default_factory=dict)

@dataclass
class ParsedDocument:
    """完整解析结果"""
    filename: str
    file_type: str
    total_pages: int
    sections: list[ParsedSection]
    metadata: dict          # {author, created_date, title, ...}
    full_text: str          # 纯文本全文

class DocumentParser:
    """文档解析引擎 - 策略模式"""

    def parse(self, file_path: Path) -> ParsedDocument:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext == ".docx":
            return self._parse_docx(file_path)
        elif ext == ".xlsx":
            return self._parse_xlsx(file_path)
        else:
            raise ValueError(f"不支持的格式: {ext}")

    def _parse_pdf(self, file_path: Path) -> ParsedDocument:
        # TODO: 用 PyPDF2 提取文本 + 表格检测
        pass

    def _parse_docx(self, file_path: Path) -> ParsedDocument:
        # TODO: 用 python-docx 提取段落/标题/表格
        pass

    def _parse_xlsx(self, file_path: Path) -> ParsedDocument:
        # TODO: 用 openpyxl 提取工作表数据
        pass
```

**测试重点**：
- 正常 PDF 解析
- 含表格的 PDF
- 中文 PDF（UTF-8 编码）
- 损坏文件异常处理
- 空文件
- DOCX 标题层级提取
- XLSX 多工作表

**验证**：`pytest tests/test_parser.py -v` → 全绿

**面试加分点**：策略模式设计、异常处理、类型注解

---

#### 任务 2.2：文本切片器

**目标**：将解析后的文档按语义边界切片，保留上下文

**文件**：
- 创建 `src/core/chunker.py`
- 创建 `tests/test_chunker.py`

**核心逻辑**：
```python
# src/core/chunker.py
from src.config import settings

class TextChunker:
    """智能文本切片 - 按段落边界切分，避免切断句子"""

    def __init__(self, chunk_size=None, overlap=None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.overlap = overlap or settings.CHUNK_OVERLAP

    def chunk(self, parsed_doc) -> list[dict]:
        """返回 [{text, metadata, chunk_index}]"""
        chunks = []
        for section in parsed_doc.sections:
            section_chunks = self._chunk_section(section)
            chunks.extend(section_chunks)
        return chunks

    def _chunk_section(self, section) -> list[dict]:
        # 按自然段落切分
        # 超过 chunk_size 时以句子边界切分
        # 相邻 chunk 保留 overlap 字符重叠
        pass
```

**验证**：`pytest tests/test_chunker.py -v`

---

#### 任务 2.3：Embedding 服务

**目标**：封装 BGE-M3 向量化，支持批量处理

**文件**：
- 创建 `src/core/embedder.py`
- 创建 `tests/test_embedder.py`

**核心**：
```python
# src/core/embedder.py
from sentence_transformers import SentenceTransformer
from src.config import settings

class Embedder:
    """BGE-M3 向量编码器（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device="cpu"
            )
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """单条查询向量化"""
        return self.embed([query])[0]
```

**测试重点**：
- 向量维度 = 1024
- 批量 vs 单条结果一致
- normalize 后 L2 范数 ≈ 1.0
- 空文本处理

**验证**：`pytest tests/test_embedder.py -v`

**注意**：此任务需要 BGE-M3 模型已在笔记本就绪（已有）

---

### 第三阶段：检索 + 入库管线（Day 6-8）

#### 任务 3.1：Qdrant 检索器

**目标**：封装 Qdrant 操作，支持语义搜索 + 元数据过滤

**文件**：
- 创建 `src/core/retriever.py`
- 创建 `tests/test_retriever.py`

**核心接口**：
```python
# src/core/retriever.py
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.config import settings
from src.core.embedder import Embedder

class Retriever:
    """Qdrant 向量检索 + 元数据过滤"""

    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.embedder = Embedder()
        self._ensure_collection()

    def search(
        self,
        query: str,
        top_k: int = None,
        filters: dict = None,  # {"file_type": "pdf", "owner_id": 1}
    ) -> list[dict]:
        """
        语义搜索 + 可选元数据过滤
        返回 [{text, metadata, score}]
        """
        pass

    def index_document(self, doc_id: int, chunks: list[dict]):
        """将切片写入 Qdrant"""
        pass

    def delete_document(self, doc_id: int):
        """删除文档的所有向量"""
        pass
```

**测试重点**（需要 Qdrant 运行）：
- 空查询
- 元数据过滤（文件类型、日期范围）
- 删除文档后检索不到

**验证**：`pytest tests/test_retriever.py -v`

---

#### 任务 3.2：文档上传 API

**目标**：POST /api/v1/documents/upload → 解析 → 切片 → 入库

**文件**：
- 创建 `src/schemas/document.py`
- 创建 `src/api/documents.py`
- 创建 `tests/test_api_documents.py`

**API 端点设计**：
```
POST   /api/v1/documents/upload     # 上传文档（multipart/form-data）
GET    /api/v1/documents/            # 文档列表（分页）
GET    /api/v1/documents/{id}        # 文档详情 + 元数据
DELETE /api/v1/documents/{id}        # 删除文档（同步删向量）
GET    /api/v1/documents/{id}/status # 处理状态查询
```

**核心逻辑**：
```python
# src/api/documents.py
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 校验文件类型和大小
    # 2. 保存到 uploads/
    # 3. 写入数据库（status=uploaded）
    # 4. 投递异步任务：解析 + 切片 + 向量化 + 入库
    # 5. 返回文档元数据（status=processing）
    pass
```

**验证**：`pytest tests/test_api_documents.py -v`

---

#### 任务 3.3：搜索 API

**目标**：POST /api/v1/search → 语义搜索 + 元数据过滤 → 返回结果

**文件**：
- 创建 `src/schemas/search.py`
- 创建 `src/api/search.py`
- 创建 `tests/test_api_search.py`

**API 设计**：
```json
// POST /api/v1/search
{
  "query": "第三季度营收数据",
  "top_k": 5,
  "filters": {
    "file_type": "xlsx",
    "date_from": "2026-01-01"
  }
}

// 响应
{
  "results": [
    {
      "document_id": 1,
      "filename": "Q3财报.xlsx",
      "chunk_text": "...",
      "score": 0.92,
      "metadata": {"sheet_name": "汇总", "row_range": "A1:D20"}
    }
  ],
  "total": 5,
  "query_time_ms": 123
}
```

**验证**：`pytest tests/test_api_search.py -v`

---

### 第四阶段：LLM 集成 + 增强功能（Day 9-11）

#### 任务 4.1：LLM 客户端（async httpx）

**目标**：封装台式机 Ollama 调用，支持流式输出

**文件**：
- 创建 `src/core/llm_client.py`
- 创建 `tests/test_llm_client.py`

**核心（async 改造）**：
```python
# src/core/llm_client.py
import httpx
from src.config import settings

class LLMClient:
    """Ollama LLM 异步客户端 — 不阻塞 FastAPI 事件循环"""

    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    async def generate(self, prompt: str, stream: bool = False) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {"num_ctx": 4096}
                }
            )
            return response.json()["response"]

    async def generate_stream(self, prompt: str):
        """流式输出 — 逐 token yield"""
        # SSE 格式返回给前端
        pass
```

**测试**：用 mock httpx 测 async 行为（不需要台式机在线）

**验证**：`pytest tests/test_llm_client.py -v`

---

#### 任务 4.2：文档对比功能

**目标**：上传两个版本文档，对比差异并生成摘要

**文件**：
- 创建 `src/core/comparator.py`
- 创建 `src/api/analysis.py`
- 创建 `tests/test_comparator.py`

**API**：
```
POST /api/v1/analysis/compare
{
  "doc_id_1": 1,
  "doc_id_2": 2
}

→ {
  "diff_summary": "v2 相比 v1：新增第3章'预算调整'，删除了附录B，修改了第2.1节金额从500万到650万...",
  "added_sections": [...],
  "removed_sections": [...],
  "modified_sections": [...]
}
```

**实现**：
1. `difflib` 做文本级差异检测
2. LLM 做差异摘要（结构化输出）
3. 返回结构化对比结果

---

#### 任务 4.3：文档自动分类（零样本）

**目标**：上传文档自动打标签（财务/人事/技术/合同...）

**文件**：
- 创建 `src/core/classifier.py`
- 添加测试到 `tests/`

**策略**：用 BGE-M3 计算文档向量与标签描述的相似度，选最高分标签

```
标签候选: ["财务报告", "人事档案", "技术文档", "合同协议", "会议纪要"]
文档向量 vs 标签描述向量 → 余弦相似度 → 取 top1
```

---

### 第五阶段：认证 + 权限 + 审计（Day 12-14）

#### 任务 5.1：用户认证（JWT）

**目标**：注册/登录/Token 刷新

**文件**：
- 创建 `src/schemas/user.py`
- 创建 `src/api/auth.py`
- 创建 `tests/test_api_auth.py`

**API**：
```
POST /api/v1/auth/register    # 注册
POST /api/v1/auth/login       # 登录 → 返回 access_token
GET  /api/v1/auth/me          # 当前用户信息
```

**测试**：注册 → 登录 → 用 token 访问受保护接口

---

#### 任务 5.2：RBAC 权限控制

**目标**：普通用户只能看自己的文档，管理员看全部

**实现**：
```python
# FastAPI Depends
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    # 解析 JWT → 查数据库 → 返回 User 对象
    pass

# 在 documents API 中
@router.get("/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_admin:
        return db.query(Document).all()  # 管理员看全部
    return db.query(Document).filter(Document.owner_id == current_user.id).all()
```

---

#### 任务 5.3：审计日志

**目标**：记录每次搜索、下载、删除操作

**文件**：
- 创建 `src/models/audit.py`
- 创建 `src/middleware/audit.py`

**审计表**：
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String(50))     # search, download, delete, upload
    resource_type = Column(String(50))  # document, search
    resource_id = Column(Integer)
    detail = Column(String(500))
    ip_address = Column(String(50))
    created_at = Column(DateTime)
```

---

### 第六阶段：Docker Compose 部署（Day 15）

#### 任务 6.1：Docker Compose 编排

**目标**：一键启动全部服务

**文件**：`docker-compose.yml`

```yaml
version: "3.8"
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment: ...
    depends_on: [redis, qdrant]

  worker:
    build: .
    command: arq src.tasks.WorkerSettings
    depends_on: [redis]

  redis:
    image: redis:7-alpine

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["./qdrant_data:/qdrant/storage"]
```

**验证**：`docker compose up -d` → `curl localhost:8000/health` → `{"status": "ok"}`

---

## 五、测试策略

### 5.1 分层测试

```
         ┌─────────────┐
         │  集成测试     │  完整链路（需要台式机）
         │  ~10%        │  仅在晚上跑
         ├─────────────┤
         │  API 测试     │  FastAPI TestClient
         │  ~30%        │  无需台式机
         ├─────────────┤
         │  单元测试     │  纯函数 / mock
         │  ~60%        │  无需任何外部服务
         └─────────────┘
```

### 5.2 测试覆盖目标

| 模块 | 覆盖率目标 | 关键测试 |
|------|----------|---------|
| config.py | 100% | 环境变量加载、默认值 |
| parser.py | 90%+ | 3 种格式 × 正常/异常/边界 |
| chunker.py | 90%+ | 中英文、长文档、空文档 |
| embedder.py | 80%+ | 维度、归一化、批量 |
| retriever.py | 80%+ | 搜索、过滤、删除 |
| API 层 | 85%+ | 正常请求、认证、错误处理 |

### 5.3 Mock 策略

```python
# 不需要台式机的测试手段
# 1. Mock Ollama HTTP 响应
@pytest.fixture
def mock_ollama(httpx_mock):
    httpx_mock.add_response(
        url="http://192.168.3.200:11434/api/generate",
        json={"response": "这是一个模拟回答"}
    )

# 2. Mock Qdrant（或用真实容器）
# 开发阶段用真实 Qdrant Docker，CI 阶段考虑 mock

# 3. 测试数据库
# 每次测试创建临时 SQLite，测试结束销毁
```

---

## 六、开发规范

### 6.1 Git 提交规范

```
feat: 新功能
fix: 修复
test: 测试
docs: 文档
refactor: 重构
chore: 构建/工具
```

### 6.2 代码规范

- 所有函数有类型注解
- 所有公共函数有 docstring
- 配置走 .env，不进代码
- 异常要显式处理，不能 silent fail

### 6.3 分支策略

```
main       ← 稳定版本，只合并 PR
develop    ← 日常开发
feat/xxx   ← 功能分支
```

---

## 七、简历输出物

项目完成后，简历上这样写：

> **Smart Doc Analyzer — 企业文档智能分析平台** | FastAPI + Qdrant + Docker
>
> - 设计并实现了多格式文档解析引擎（PDF/Word/Excel），支持表格提取与结构化存储
> - 基于 ARQ + Redis 构建异步任务队列，解决大文档解析阻塞 API 的问题
> - 实现了混合检索（语义搜索 + 元数据过滤），查询延迟 < 500ms
> - 集成 JWT + RBAC 权限控制，实现多用户隔离与审计日志
> - pytest 测试覆盖率 > 85%，Docker Compose 一键部署
> - **技术栈**：Python, FastAPI, SQLAlchemy, Qdrant, BGE-M3, Redis, ARQ, Docker

---

## 八、风险与注意事项

| 风险 | 应对 |
|------|------|
| 台式机不在线无法跑集成测试 | 单元测试 + mock 覆盖 90% 场景，集成测试仅晚上跑 |
| PDF 解析中文乱码 | 用 PyPDF2 而非 pdfplumber（更轻量），加 encoding 检测 |
| ARQ 任务失败无重试 | 配置 max_retries=3，失败记录到数据库 |
| Excel 大文件内存溢出 | 限制文件 50MB，流式读取大工作表 |
| Qdrant 容器占用端口冲突 | 用不同端口或网络隔离 |

---

## 九、下一步行动

1. **确认**：本计划中的功能范围和技术选型是否 OK？
2. **调整**：功能太多/太少？哪个模块你最想先做？
3. **启动**：确认后从第一阶段 Day 1 开始执行
