"""配置管理 — Pydantic Settings，所有敏感信息走 .env"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ========== 应用 ==========
    APP_NAME: str = "Smart Doc Analyzer"
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 9876
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ========== 数据库 ==========
    DATABASE_URL: str = "sqlite:///./data/smart_doc.db"

    # ========== Qdrant 向量库 ==========
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "smart_docs"

    # ========== LLM ==========
    LLM_PROVIDER: str = "ollama"            # ollama | deepseek
    OLLAMA_HOST: str = "http://192.168.3.200:11434"
    OLLAMA_MODEL: str = "qwen3.6:35b-a3b"
    DEEPSEEK_API_KEY: str = ""              # 仅 provider=deepseek 时需要

    # ========== Embedding 模型（笔记本 CPU） ==========
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024
    HF_ENDPOINT: str = "https://hf-mirror.com"

    # ========== 文件上传 ==========
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ========== 文本切片 ==========
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # ========== 检索 ==========
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# 全局单例，整个项目 import 这一个实例
settings = Settings()
