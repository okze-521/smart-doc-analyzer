"""RAG 检索 API — 文档入库 + 查询"""

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.core.ingest_service import IngestService
from src.core.search_service import SearchService
from src.core.reranker import Reranker
from src.config import settings
from src.repositories.document import DocumentRepository
from src.schemas.api import SearchRequest, SearchResponse, DocumentResponse, DocumentListResponse
from src.core.llm_client import LLMClient

router = APIRouter(prefix="/api/v1", tags=["rag"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}


def get_ingest_service() -> IngestService:
    return IngestService()


def get_search_service() -> SearchService:
    reranker = None
    if settings.RERANKER_MODEL:
        reranker = Reranker(settings.RERANKER_MODEL)
    return SearchService(reranker=reranker)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    db: Annotated[Session, Depends(get_db)],
    ingest: Annotated[IngestService, Depends(get_ingest_service)],
):
    """上传文档 → 解析 → 切片 → 向量化 → 入库"""
    # 校验扩展名
    if not file.filename:
        raise HTTPException(400, "缺少文件名")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件格式: {ext}，支持 {ALLOWED_EXTENSIONS}")

    # 写入临时文件
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        # 1. 写入数据库
        repo = DocumentRepository(db)
        doc = repo.create(str(tmp_path), file.filename, ext[1:])

        # 2. 入库到 Qdrant
        result = ingest.ingest(tmp_path)

        # 3. 更新状态
        repo.update_status(doc.id, "completed")

        return {
            "document_id": doc.id,
            "filename": result["filename"],
            "file_type": result["file_type"],
            "chunk_count": result["chunk_count"],
            "status": "completed",
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/documents/search", response_model=SearchResponse)
async def search_documents(
    req: SearchRequest,
    search: Annotated[SearchService, Depends(get_search_service)],
):
    """检索相关文档片段"""
    result = search.search(req.query, top_k=req.top_k)
    return SearchResponse(**result)


# ── RAG 问答（检索 + LLM 生成） ──────────

@router.post("/documents/qa")
async def ask_question(
    req: SearchRequest,
    search: Annotated[SearchService, Depends(get_search_service)],
):
    """检索 + LLM 生成回答"""
    # 1. 检索
    result = search.search(req.query, top_k=req.top_k)
    chunks = result["chunks"]

    if not chunks:
        return {"query": req.query, "answer": "没有找到相关文档，请先上传文档。", "snippets": []}

    # 2. 拼接上下文 + LLM 生成
    context = [c["text"] for c in chunks]
    client = LLMClient()
    answer = await client.generate_with_context(req.query, context)

    return {
        "query": req.query,
        "answer": answer,
        "snippets": [
            {"text": c["text"][:200], "source": c["source_file"], "score": c["score"]}
            for c in chunks
        ],
    }


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    db: Annotated[Session, Depends(get_db)],
    offset: int = 0,
    limit: int = 20,
):
    """列出已入库文档"""
    repo = DocumentRepository(db)
    items = repo.list_all(offset=offset, limit=limit)
    return DocumentListResponse(
        total=len(items),
        items=[DocumentResponse.model_validate(d) for d in items],
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """获取单个文档详情"""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return DocumentResponse.model_validate(doc)
