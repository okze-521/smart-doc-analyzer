"""FastAPI 入口"""

from fastapi import FastAPI

from src.config import settings
from src.api.rag import router as rag_router
from src.api.analysis import router as analysis_router
from src.api.auth import router as auth_router

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
)

app.include_router(rag_router)
app.include_router(analysis_router)
app.include_router(auth_router)


@app.get("/health")
async def health():
    """存活探针"""
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
