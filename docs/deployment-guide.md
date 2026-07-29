# Smart Doc Analyzer 部署手册

> 从零开始，在任意 Linux 服务器上完成 SDA（智能文档分析器）的私有化部署。

---

## 📋 部署前检查清单

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ / Debian 11+ |
| Docker | ≥ 20.10 |
| Docker Compose | ≥ 2.0（`docker compose` 子命令可用） |
| 磁盘空间 | ≥ 10 GB（代码 + 模型 + Qdrant 数据） |
| 内存 | ≥ 8 GB（含 Embedding + Reranker 推理） |
| 网络 | 能访问 LLM 地址（内网 API 或 Ollama 主机） |

---

## 🗂️ 第一步：打包交付物（在你自己电脑上操作）

需要从 `D:\Projects\smart-doc-analyzer\` 拷贝以下文件到目标服务器。

### 必须拷贝的文件清单

> ⚠️ Dockerfile 必须拷！没有它，目标服务器无法构建 Docker 镜像。

```
smart-doc-analyzer/
├── Dockerfile              ← 镜像构建说明书
├── docker-compose.yml      ← 容器编排（一键启动）
├── pyproject.toml          ← Python 依赖声明
├── .env                    ← 环境配置（拷过去后要改 LLM 地址）
├── chat.html               ← 聊天前端页面
├── src/                    ← 全部源码
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── api/
│   ├── core/
│   ├── middleware/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   └── tasks/
├── scripts/                ← 容器启动脚本（entrypoint.sh + init_db.py）
└── models/                 ← 约 4.5 GB，可用 U 盘拷贝
    ├── bge-small/          ← Embedding 模型（95 MB）
    └── bge-reranker-v2-m3/ ← Reranker 精排模型（2.27 GB）
```

### 不需要拷贝的文件

```
.git/           ← Git 历史（目标环境不需要）
__pycache__/    ← Python 缓存（目标环境会重新生成）
.coverage       ← 测试覆盖率报告
tests/          ← 单元测试（生产环境不需要）
docs/           ← 文档（可选）
.env.example    ← 模板参考（可选）
```

### 打包命令（在你电脑上）

```bash
# 方式一：打 tar 包，然后 scp / U 盘拷走
cd /d/Projects/smart-doc-analyzer
tar -czf sda-deploy.tar.gz \
    Dockerfile \
    docker-compose.yml \
    pyproject.toml \
    .env \
    chat.html \
    src/ \
    scripts/ \
    models/

# 方式二：如果是推到公司内网 Git，直接 clone 即可
# （但 models/ 通常不上传 Git，因为太大，需单独拷贝）
```

---

## 🖥️ 第二步：目标服务器环境准备

### 2.1 安装 Docker

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER    # 免 sudo 执行 docker（需重新登录生效）

# CentOS / RHEL
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# 验证安装
docker --version
# 应输出类似：Docker version 24.0.7
```

### 2.2 安装 Docker Compose（如果 `docker compose` 不可用）

```bash
# Docker 20.10+ 自带 Compose 插件，直接可用
docker compose version
# 如果报错，手动安装：
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 📁 第三步：部署文件到目标服务器

### 3.1 创建目录并解压

```bash
# 在目标服务器上
mkdir -p /opt/smart-doc-analyzer
cd /opt/smart-doc-analyzer

# 把 sda-deploy.tar.gz 传上来后解压
tar -xzf sda-deploy.tar.gz

# 确认文件完整
ls -la
# 应看到：Dockerfile  docker-compose.yml  pyproject.toml  .env  chat.html  src/  models/
```

### 3.2 修改环境配置（关键步骤！）

```bash
vim .env   # 或用 nano .env
```

**必须改的配置项：**

```ini
# ── 1. LLM 接入（最重要） ──
# 情况 A：公司给了 OpenAI 兼容 API
LLM_PROVIDER=openai
OPENAI_API_BASE=https://公司内网地址/v1
OPENAI_API_KEY=公司分配的密钥

# 情况 B：公司有 Ollama 服务
LLM_PROVIDER=ollama
OLLAMA_HOST=http://10.x.x.x:11434
OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M

# 情况 C：连云端 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的Key

# ── 2. 安全密钥（随机生成一个） ──
SECRET_KEY=替换成一个至少32位的随机字符串
# 生成方法：openssl rand -hex 32
```

---

## 🚀 第四步：启动服务

### 4.1 构建并启动

```bash
cd /opt/smart-doc-analyzer

# 第一次部署（需要构建镜像，约 3-5 分钟）
docker compose up -d --build

# 后续重启（代码/配置有改动时）
docker compose up -d
```

### 4.2 验证服务

```bash
# 1. 检查容器状态（两个服务都应该是 Up）
docker compose ps

# 期望输出：
# NAME                        STATUS
# smart-doc-analyzer-app-1    Up (healthy)
# smart-doc-analyzer-qdrant-1  Up

# 2. 检查日志（确认没报错）
docker compose logs app | tail -20

# 期望看到：
# Uvicorn running on http://0.0.0.0:8000

# 3. 访问 API
curl http://localhost:9876/health
# 期望返回：{"status":"ok"}

# 4. 检查 Qdrant 是否就绪
curl http://localhost:6333/health
# 期望返回：{"title":"qdrant - vector search engine","version":"1.8.4"}
```

### 4.3 如果报错

| 现象 | 原因 | 解决 |
|------|------|------|
| `app-1` 状态 Exited | LLM 连不上 | 检查 `.env` 里的 LLM 地址和密钥 |
| `app-1` 报 `Model not found` | 模型路径不对 | 检查 `models/` 是否完整拷贝 |
| 端口 9876 访问不了 | 防火墙拦截 | `sudo ufw allow 9876` 或 `sudo firewall-cmd --add-port=9876/tcp` |
| `qdrant` 没起来 | 端口冲突 | `sudo lsof -i :6333` 查谁占用了 |

---

## 🔄 第五步：后续更新流程

### 代码有改动时

```bash
# 方式一：如果有镜像仓库
# 在你电脑上：docker build -t 仓库地址/sda:v2 . && docker push 仓库地址/sda:v2
# 在服务器上：改 docker-compose.yml 里的 image，然后 docker compose up -d

# 方式二：直接拷贝新代码
# 把改过的 src/ 文件传到服务器，然后：
cd /opt/smart-doc-analyzer
docker compose up -d --build
```

### 只改配置时（不改代码）

```bash
# 改 .env 后
docker compose up -d    # 自动重建受影响的容器
```

### 日常维护

```bash
# 查看所有容器状态
docker compose ps

# 查看实时日志
docker compose logs -f app

# 停止服务
docker compose down

# 完全清理（删除容器+数据卷，⚠️ 数据会丢失）
docker compose down -v
```

---

## 📊 架构总结

```
目标服务器（笔记本 / 云主机）
┌──────────────────────────────────────────────┐
│  docker compose                              │
│                                              │
│  ┌──────────────┐   ┌──────────────────┐     │
│  │  app 容器     │   │  qdrant 容器      │     │
│  │  FastAPI:8000 │◄──│  Qdrant v1.8.4   │     │
│  │              │   │  Port 6333       │     │
│  │  ├─ Embedding │   └──────────────────┘     │
│  │  ├─ Reranker  │                            │
│  │  └─ LLM Client│──► 公司内网 LLM API        │
│  └──────────────┘      (或 Ollama 主机)        │
│         │                                     │
│         ▼                                     │
│  /opt/smart-doc-analyzer/models/ (挂载)        │
│  /opt/smart-doc-analyzer/data/    (数据卷)      │
└──────────────────────────────────────────────┘
```

---

## 🎯 面试话术

> "SDA 的交付流程是：目标服务器安装 Docker 后，拷贝三个东西——编排文件、模型文件和配置文件。修改 `.env` 里的 LLM 地址和密钥，一条 `docker compose up -d` 就起来了。LLM 层和环境完全解耦，切换本地 Ollama 或公司内网 API 只需改一行配置。整个部署不需要安装 Python，不需要配虚拟环境，有 Docker 就能跑。"
