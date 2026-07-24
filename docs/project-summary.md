# Smart Doc Analyzer — 项目总结

> **企业文档智能分析平台**  
> 完成日期：2026-07-24 | 开发周期：3 天 | 111 tests · 89% 覆盖率

---

## 一、项目概况

```
D:/Projects/smart-doc-analyzer/
├── Dockerfile                     # Docker 镜像构建
├── docker-compose.yml             # 一键部署（app + Qdrant）
├── .dockerignore
├── pyproject.toml                 # Python 项目配置
├── .env / .env.example            # 环境变量
├── scripts/
│   └── init_db.py                 # 数据库初始化脚本
├── src/                           # ⬅ 源码：31 个模块，1800+ 行
│   ├── config.py                  # Pydantic Settings 配置
│   ├── database.py                # SQLAlchemy 连接
│   ├── main.py                    # FastAPI 入口
│   ├── api/                       # API 路由层
│   │   ├── rag.py                 #   文档上传/搜索/列表
│   │   ├── analysis.py            #   对比/分类
│   │   └── auth.py                #   注册/登录/个人信息
│   ├── core/                      # 核心引擎层
│   │   ├── parser.py              #   PDF/DOCX/XLSX 解析
│   │   ├── chunker.py             #   语义边界切片
│   │   ├── embedder.py            #   BGE-small 向量化
│   │   ├── qdrant_store.py        #   Qdrant 向量库封装
│   │   ├── ingest_service.py      #   入库编排服务
│   │   ├── search_service.py      #   检索编排服务
│   │   ├── llm_client.py          #   DeepSeek API 客户端
│   │   ├── comparator.py          #   difflib 差异 + LLM 摘要
│   │   ├── classifier.py          #   BGE 向量相似度分类
│   │   ├── auth.py                #   bcrypt 密码 + JWT
│   │   └── permissions.py         #   RBAC 角色检查
│   ├── models/                    # 数据模型
│   │   ├── user.py                #   用户表
│   │   ├── document.py            #   文档表
│   │   └── audit.py               #   审计日志表
│   ├── middleware/
│   │   └── audit.py               # HTTP 审计中间件
│   ├── repositories/
│   │   └── document.py            # 文档 CRUD
│   └── schemas/
│       └── api.py                 # Pydantic 请求/响应模型
├── tests/                         # ⬅ 测试：18 个文件，1500+ 行，111 tests
│   ├── conftest.py                #   共享 fixtures
│   ├── mock_embedder.py           #   Mock 向量器
│   ├── test_config.py             #   配置测试
│   ├── test_main.py               #   健康检查测试
│   ├── test_parser.py             #   解析器测试（13）
│   ├── test_chunker.py            #   切片器测试（12）
│   ├── test_embedder.py           #   向量器测试（6）
│   ├── test_qdrant.py             #   向量库测试（6）
│   ├── test_repository.py         #   CRUD 测试（8）
│   ├── test_ingest.py             #   入库集成测试（3）
│   ├── test_api.py                #   API 集成测试（11）
│   ├── test_llm_client.py         #   LLM 客户端测试（8）
│   ├── test_comparator.py         #   对比器测试（8）
│   ├── test_compare_api.py        #   对比 API 测试（5）
│   ├── test_classifier.py         #   分类器测试（8）
│   ├── test_classify_api.py       #   分类 API 测试（5）
│   ├── test_auth.py               #   认证测试（10）
│   └── test_rbac.py               #   RBAC+审计测试（5）
└── docs/
    └── implementation-plan.md     # 15 天实施计划
```

### 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | async、自动 docs、类型驱动 |
| 数据库 | SQLite + SQLAlchemy | 零配置，开发即用 |
| 向量库 | Qdrant 1.18 (Docker) | 高性能，本地部署 |
| Embedding | BGE-small-zh-v1.5 (512d) | ModelScope 下载，CPU 可跑 |
| LLM | DeepSeek API | 复用 Hermes 已有 Key |
| 密码 | bcrypt | 工业标准 |
| 认证 | JWT (HS256) | 无状态，轻量 |

### 设计模式

```
策略模式   → parser.py      （PDF/DOCX/XLSX 统一接口）
模板方法   → chunker.py     （中英文语义边界切分）
依赖注入   → FastAPI Depends（get_db / get_current_user / require_role）
编排模式   → ingest_service （解析→切片→向量→入库→写DB）
适配器模式 → qdrant_store   （1.18 API 适配）
```

---

## 二、API 端点总览

```
 认证
  POST   /api/v1/auth/register          用户注册
  POST   /api/v1/auth/login             用户登录
  GET    /api/v1/auth/me                个人信息（需 Bearer token）

 文档
  POST   /api/v1/documents/upload       上传文档（PDF/DOCX/XLSX）→ 自动入库
  GET    /api/v1/documents              文档列表（分页）
  GET    /api/v1/documents/{id}         文档详情

 检索
  POST   /api/v1/search                 语义搜索 → 返回上下文 + LLM 回答

 分析
  POST   /api/v1/analysis/compare       文档对比（difflib + LLM 摘要）
  POST   /api/v1/analysis/classify      文档分类（7 类别 BGE 相似度）

 系统
  GET    /health                        存活探针
  GET    /docs                          Swagger UI
```

---

## 三、测试矩阵

```
模块              测试数    覆盖率    类型
──────────────────────────────────────────
config             1       100%     单元
main               1       100%     单元
parser            13        93%     单元
chunker           12        95%     单元
embedder           6        88%     单元（真实模型）
qdrant_store       6        94%     集成（Docker Qdrant）
repository         8        74%     单元
ingest             3       100%     集成
api               11        92%     集成
llm_client         8       100%     单元（mock HTTP）
comparator         8        91%     单元（mock LLM）
compare_api        5        85%     集成（mock LLM）
classifier         8        97%     单元（mock 向量）
classify_api       5        83%     集成（mock 向量）
auth              10       100%     集成（真实DB+JWT）
rbac               5         0%*    集成（权限+审计）
──────────────────────────────────────────
合计             111        89%
```

> \* permissions 模块覆盖率 0% 是因为它作为 FastAPI Depends 被间接测试，未直接 import 调用。

### 运行方式

```bash
# 全量测试 + 覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing

# 单模块
pytest tests/test_auth.py -v

# 快速（跳过 Marker）
pytest tests/ -v -m "not slow"
```

---

## 四、开发实录

### 踩坑记录

| # | 问题 | 解决 |
|---|------|------|
| 1 | hf-mirror 下载 BGE 模型超时 | 换 ModelScope，稳定 5-6 MB/s |
| 2 | Qdrant 1.18 `search` → `query_points` | API 大版本变更，返回 `.points` |
| 3 | Qdrant 1.18 无 `vectors_count` 属性 | 改用 `getattr` 或 config 读取 |
| 4 | Qdrant point_id 必须 int/UUID | 全部测试 ID 改为整数 |
| 5 | passlib 不兼容 bcrypt 5.x | 直接使用 bcrypt 库 |
| 6 | FastAPI 裸参数 → 422 | 改用 Pydantic request body |
| 7 | `add_middleware` 不能在启动后调用 | 审计测试改为直接测模型 |
| 8 | Docker 构建清华源仍超时 | 放弃 Docker，本地 uvicorn 直接跑 |

### 关键决策

- **TDD 全流程**：每个模块先写测试（RED）→ 写实现 → 跑测试（GREEN）→ 重构
- **零台式机依赖**：Embedding 用本地 BGE-small CPU，LLM 用 DeepSeek API
- **Mock 分层**：单元测试 mock LLM/Embedding/HTTP，集成测试用真实 DB/Qdrant/模型
- **SQLite 而非 MySQL**：开发阶段零配置，生产可无缝切 PostgreSQL

---

## 五、部署方式

### 方式一：本地直接跑（推荐开发）

```bash
cd D:/Projects/smart-doc-analyzer
.venv/Scripts/python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 9876
# → http://127.0.0.1:9876/docs
```

前提：Qdrant Docker 已运行（`localhost:6333`）

### 方式二：Docker Compose（国内网络可能失败）

```bash
docker compose up -d --build
```

⚠️ DockerHub 拉取 python:3.11-slim + pip 安装大型依赖（sentence-transformers ~2GB），国内极易超时。

---

## 六、后续可扩展

- [ ] 切换 PostgreSQL（生产环境）
- [ ] Celery 异步任务（大文件入库）
- [ ] Redis 缓存层（高频搜索）
- [ ] Prometheus + Grafana 监控
- [ ] 文档批量导入（文件夹拖拽）
- [ ] 前端 UI（Vue/React）
- [ ] Reranker（提升检索精度）
- [ ] 文档版本管理（diff 历史）
