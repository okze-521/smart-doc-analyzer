# Smart Doc Analyzer

> 智能文档分析平台 — 上传文档，AI 问答，全文对比

[![CI](https://github.com/okze-521/smart-doc-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/okze-521/smart-doc-analyzer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 核心能力

| 功能 | 描述 |
|------|------|
| 📄 文档解析 | 支持 PDF / DOCX / XLSX |
| 🧠 语义检索 | BGE-small 向量化 + Qdrant 向量库 |
| 🎯 重排序 | BGE-Reranker-v2-m3 Cross-Encoder 精排 |
| 💬 AI 问答 | Ollama 本地 LLM（qwen3.6:35b）+ DeepSeek 兜底 |
| 🔍 文档对比 | 上传两个文档，AI 自动生成差异摘要 |

## 技术栈

```
┌─────────────────────────────────────┐
│          笔记本电脑 (Docker)          │
│  FastAPI + Qdrant v1.8.4             │
│  BGE-small-zh-v1.5 (Embedding 512维)│
│  BGE-Reranker-v2-m3 (精排)           │
└─────────────────────────────────────┘
              │ LLM 请求
              ▼
┌─────────────────────────────────────┐
│      台式机 RTX 5090D (Ollama)        │
│  qwen3.6:35b-a3b-q4_K_M (23.9G)     │
└─────────────────────────────────────┘
```

## 快速开始

```bash
# 1. 下载模型（只需一次）
python -c "from modelscope import snapshot_download; snapshot_download('BAAI/bge-reranker-v2-m3', cache_dir='./models')"

# 2. 启动
docker compose up -d

# 3. 打开浏览器
open http://localhost:9876
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `ollama` | `ollama` 或 `deepseek` |
| `OLLAMA_HOST` | `http://192.168.3.200:11434` | Ollama 地址 |
| `OLLAMA_MODEL` | `qwen3.6:35b-a3b-q4_K_M` | 模型名 |
| `EMBEDDING_MODEL` | `/app/models/bge-small` | Embedding 路径 |
| `EMBEDDING_DIM` | `512` | 向量维度 |
| `RERANKER_MODEL` | `/app/models/bge-reranker-v2-m3` | 精排模型（留空=跳过） |
| `QDRANT_HOST` | `qdrant` | Qdrant 地址 |
| `DATABASE_URL` | `sqlite:///./data/smart_doc.db` | 数据库 |

完整配置见 [`.env.example`](.env.example)。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/v1/documents/upload` | 上传文档 |
| `GET` | `/api/v1/documents` | 文档列表 |
| `POST` | `/api/v1/documents/search` | 语义检索 |
| `POST` | `/api/v1/documents/qa` | **AI 问答**（检索+精排+LLM） |
| `POST` | `/api/v1/analysis/diff` | 文档对比 |
| `GET` | `/docs` | Swagger UI |

### QA 示例

```bash
curl -X POST http://localhost:9876/api/v1/documents/qa \
  -H "Content-Type: application/json" \
  -d '{"query": "这个项目用了哪些技术？", "top_k": 3}'
```

```json
{
  "query": "这个项目用了哪些技术？",
  "answer": "该项目使用 FastAPI + Qdrant v1.8.4 + BGE-small...",
  "chunks": [
    {"text": "...", "score": 0.85, "source_file": "README.md", ...}
  ]
}
```

## 开发

```bash
uv sync
uv run pytest -v           # 111 个测试
uv run ruff check src/     # 代码检查
```

## 许可证

MIT © 张钰泽 (okze-521)
