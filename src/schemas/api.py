"""API 请求/响应模型"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── 文档上传 ──────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_type: str
    chunk_count: int
    status: str
    created_at: datetime


# ── 检索 ──────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=50)
    history: list[dict[str, str]] | None = None  # [{role, content}] 多轮对话历史，最多 10 轮


class SearchChunk(BaseModel):
    chunk_index: int
    text: str
    score: float
    source_file: str


class SearchResponse(BaseModel):
    query: str
    total_hits: int
    chunks: list[SearchChunk]


# ── 文档详情 ──────────────────────────────

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str | None = None
    file_type: str
    status: str
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]


# ── 文档对比 ──────────────────────────────

class CompareRequest(BaseModel):
    doc_id_1: int | None = None
    doc_id_2: int | None = None
    text_1: str | None = None
    text_2: str | None = None


class CompareResponse(BaseModel):
    identical: bool
    diff_type: str
    line_changes: int
    added_lines: list[str]
    removed_lines: list[str]
    summary: str | None = None


# ── 文档分类 ──────────────────────────────

class ClassifyRequest(BaseModel):
    text: str | None = None
    doc_id: int | None = None


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    all_scores: dict[str, float]
