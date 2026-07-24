"""分析 API（文档对比、分类等）"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.api import CompareRequest, CompareResponse, ClassifyRequest, ClassifyResponse
from src.core.comparator import Comparator
from src.core.classifier import DocumentClassifier
from src.core.llm_client import LLMClient
from src.core.embedder import TextEmbedder
from src.repositories.document import DocumentRepository

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def get_comparator():
    """注入 Comparator（测试时可覆盖）"""
    llm = LLMClient()
    return Comparator(llm_client=llm)


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(
    req: CompareRequest,
    db: Session = Depends(get_db),
    comparator: Comparator = Depends(get_comparator),
):
    """对比两个文档并生成摘要"""
    repo = DocumentRepository(db)

    if req.doc_id_1 and req.doc_id_2:
        # 从数据库加载文档文本
        doc1 = repo.get_by_id(req.doc_id_1)
        doc2 = repo.get_by_id(req.doc_id_2)
        if not doc1 or not doc2:
            raise HTTPException(404, "文档未找到")
        text1 = doc1.content or ""
        text2 = doc2.content or ""
    elif req.text_1 and req.text_2:
        text1 = req.text_1
        text2 = req.text_2
    else:
        raise HTTPException(400, "请提供 doc_id_1/doc_id_2 或 text_1/text_2")

    diff = comparator.compare_texts(text1, text2)

    # LLM 摘要
    if comparator.llm:
        summary = await comparator.summarize_diff(text1, text2, diff)
    else:
        summary = None

    return CompareResponse(
        identical=diff["identical"],
        diff_type=diff["diff_type"],
        line_changes=diff["line_changes"],
        added_lines=diff.get("added_lines", []),
        removed_lines=diff.get("removed_lines", []),
        summary=summary,
    )


# ── 分类 ───────────────────────────────────

DEFAULT_CATEGORIES = {
    "合同": "合同协议法律条款签署甲乙双方违约赔偿",
    "财务报表": "财务收入支出利润资产负债表现金流量审计",
    "技术文档": "API接口技术文档代码开发架构部署运维",
    "简历": "简历求职工作经验教育背景技能证书",
    "报告": "报告分析总结数据统计趋势调研评估",
    "通知公告": "通知公告公示决定批复函件",
    "其他": "通用文档杂项综合",
}


def get_classifier():
    """注入 Classifier（测试时可覆盖）"""
    embedder = TextEmbedder()
    return DocumentClassifier(embedder, DEFAULT_CATEGORIES)


@router.post("/classify", response_model=ClassifyResponse)
async def classify_document(
    req: ClassifyRequest,
    classifier: DocumentClassifier = Depends(get_classifier),
):
    """对文本或文档 ID 进行自动分类"""
    text = req.text
    if req.doc_id is not None:
        from src.database import SessionLocal
        from src.repositories.document import DocumentRepository
        db = SessionLocal()
        try:
            repo = DocumentRepository(db)
            doc = repo.get_by_id(req.doc_id)
            if not doc:
                raise HTTPException(404, "文档未找到")
            text = doc.content or ""
        finally:
            db.close()

    if not text:
        raise HTTPException(400, "无文本内容可分类")

    result = classifier.classify(text)
    return ClassifyResponse(**result)
