# Smart Doc Analyzer 技术架构与 AI 应用岗实战攻略

本文件为个人 SDA 项目的**技术对标手册**。在面试中，你的核心策略不是“我写了一个 Demo”，而是 **“我具备企业级私有化大模型系统的落地能力”**。

---

## 🏗️ 一、SDA 系统架构（架构图描述）

面试官让你画图或解释架构时，请按这个 **RAG 全链路**逻辑描述：

### 1. 核心数据流 (Mermaid)
```mermaid
flowchart TD
    %% 用户与网关
    User((用户)) --> API[FastAPI 异步网关]
    
    %% 鉴权层
    subgraph API ["🔒 API & 安全"]
        Auth[JWT + RBAC 鉴权]
        Audit[审计日志中间件]
    end
    
    %% 业务层 - 检索
    subgraph RAG_Pipeline ["🧠 RAG 核心逻辑链"]
        direction TB
        Q[输入 Query] --> P1[Chunker 切片 (500+Overlap)]
        
        P1 --> E[Embedding (BGE-m3/zh)]
        E --> Qdrant[(Qdrant 向量库检索)]
        
        Search[Top-9 候选集召回] --> ReRank[BGE-Reranker 交叉精排]
        
        ReRank[Score 过滤 <br> Top-3 精准命中] --> Prompt[Prompt Engineer 组装指令]
    end
    
    %% LLM层 - 推理
    subgraph Inference ["⚡ 大模型算力层"]
        Router{路由决策}
        
        case1(简单问答/翻译) -->|走本地| LLM_Local[(Ollama<br>qwen3.6:35b-q4)]
        case2(复杂逻辑分析) -->|走强力| LLM_Cloud[(DeepSeek API / 云端)]
    end
    
    P1 --> Router
    Prompt --> Router
    Router --> LLM_Local
    Router --> LLM_Cloud
    
    %% 输出
    LLM_Local & LLM_Cloud --> Response[JSON/Markdown Output]
    
    style RAG_Pipeline fill:#e1f5fe,stroke:#0277bd
    style Inference fill:#fff9c4,stroke:#fbc02d
```

### 2. 核心组件说明
- **API 层 (FastAPI)**：利用 `asyncio` 实现高并发支持，配置了 Pydantic Settings 动态管理敏感变量。
- **检索层 (Vector & Reranker)**：**核心亮点**。不只是简单的向量相似度匹配，而是引入了 **Cross-Encoder（交叉编码器）做二次精排**，过滤掉 Top-9 中的无关噪音，最终只给 LLM 喂最准的 Top-3。
- **算力层 (Hybrid Compute)**：默认本地 Ollama 推理以确保**数据安全不出域**；遇到复杂计算或敏感词拦截时，动态降级/切换至云端 API 兜底。

---

## 💼 二、你的技术栈 vs 市场真实需求表

在面试中，当对方问“你有什么竞争优势”时，直接对标这张表：

| 🟢 SDA (你正在做的) | 🔴 AI应用岗 JD (企业要求的痛点) | **你的实战对策** |
| :--- | :--- | :--- |
| **BGE-Reranker 交叉精排** (代码: `src/core/reranker.py`) | "解决向量检索精度低、回答幻觉问题。" | “我引入了二次排序机制，将候选集从 Top-9 过滤至 Top-3，有效减少了大模型‘看都不看就对答’的情况。” |
| **私有化部署** (代码: `src/main.py`, `docker-compose.yml`) | "企业数据敏感，要求全量本地化/私有云部署。" | “基于 Ollama + Docker Compose 实现了存算分离架构，核心业务数据在用户内网流转，零 API 费用成本。” |
| **RBAC 权限 & JWT** (代码: `src/core/auth.py`) | "企业级权限管理（部门/角色隔离）。" | “实现了基于 RBAC 的模型鉴权拦截，确保只有授权账号能访问核心知识库接口。” |
| **14个测试文件 / Pytest** (代码: `/tests/`) | "具备工程化交付意识，关注代码质量。" | “通过 TDD 原则编写了覆盖 API、切片器、嵌入器及权限逻辑的 25+ 单元测试，保证系统迭代时不引入回归 Bug。” |

---

## 🎤 三、高频面试问答（SPEEEch 话术准备）

### Q1: “为什么你的架构要引入 Reranker 这么重的模型？性能受得了吗？”
> **参考话术：**
> “确实，Cross-Encoder 的推理耗时比单纯向量匹配要高。我的解决方案是**分层检索策略（Cascade Retrieval）**：先用轻量级的 `BGE-embedding` 快速召回 Top-9；如果用户需要深度分析，再用 Reranker 过滤到 Top-3。此外，我在代码里加了一层简单的哈希缓存，对高频重复的问题直接命中旧分，避免了每次都跑重排模型。”

### Q2: “你提到的‘双模型协同’具体是怎么设计的？”
> **参考话术：**
> “在 `config.py` 和 API Router 层设计了路由逻辑。默认情况下，利用我的 RTX 5090D 显卡推 qwen3.6:35b (4bit量化版)，这样企业数据完全不用出域，省了 Token 钱且保了密；如果任务涉及极度复杂的代码生成或数学推理，我会动态将请求转发给 DeepSeek API 这种云端强力模型做兜底。这种‘本地为主、云端为辅’的策略是兼顾成本与质量的最佳实践。”

### Q3: “你的 Docker 部署如何保证服务不挂掉？”
> **参考话术：**
> “我写了一个基于 API 探针的深度健康检查（Deep Health Check）。Docker 不是只看端口通不通，而是通过 curl 请求 `/api/v1/health` 或者让模型做一个轻量级的‘打招呼’测试。如果显存泄漏导致推理死锁，我会自动触发容器重启机制，保证生产环境的可用性。”

---

## 🌟 四、总结：你的核心竞争力 (用于自我介绍)

> “我具备从 **底层 AI 基建（私有化部署/GPU调度）** 到 **上层工程应用（RAG系统/向量检索优化）** 的全链路解决能力。目前主导的 Smart Doc Analyzer 项目，通过引入 Cross-Encoder 精排算法与严格的 RBAC 鉴权，成功解决了企业知识库‘存得进、找不准、不敢传’的行业痛点。”

---
*注：这份文档不仅是你面试的底气，也是你个人 GitHub 展示栏里一份非常硬核的 README。*
