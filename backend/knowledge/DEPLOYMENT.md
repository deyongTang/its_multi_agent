# ITS Knowledge 知识库平台 Docker 部署指南

本文档提供 ITS Knowledge 知识库平台的 Docker 部署完整指南。

## 目录

- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [维护与监控](#维护与监控)

---

## 前置要求

在开始部署之前，请确保远程服务器已安装以下软件：

### 必需软件

- **Docker**: 版本 20.10 或更高
- **Docker Compose**: 版本 2.0 或更高
- **Git**: 用于拉取代码

### 检查安装

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker compose version

# 检查 Git 版本
git --version
```

### 安装 Docker（如果未安装）

**Ubuntu/Debian:**
```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**
```bash
# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER
```

---

## 快速开始

本项目提供了两种部署方式：

### 方式 1: 使用部署脚本（推荐）

**本地/首次部署：**
```bash
# 克隆项目
git clone https://github.com/deyongTang/its_multi_agent.git
cd its_multi_agent/backend/knowledge

# 配置环境变量
cp .env.example .env
vim .env  # 编辑配置文件

# 运行部署脚本
bash deploy.sh
```

**远程服务器自动部署：**
```bash
# SSH 登录到服务器
ssh user@your-server-ip

# 首次部署：克隆项目到 /opt/its_multi_agent
cd /opt
git clone https://github.com/deyongTang/its_multi_agent.git
cd its_multi_agent/backend/knowledge

# 配置环境变量
cp .test-env.example .test-env
vim .test-env  # 编辑配置文件

# 运行自动部署脚本
bash deploy-auto.sh
```

**GitHub Actions 自动部署：**
```bash
# 在 GitHub 仓库页面：Actions → Deploy Knowledge Platform → Run workflow
# 或者推送代码到 main 分支的 backend/knowledge/ 目录会自动触发部署
```

### 方式 2: 手动部署

```bash
# 1. 克隆项目
git clone https://github.com/deyongTang/its_multi_agent.git
cd its_multi_agent/backend/knowledge

# 2. 配置环境变量
cp .env.example .env
vim .env

# 3. 构建并启动
docker-compose build
docker-compose up -d

# 4. 查看状态
docker-compose ps
docker-compose logs -f
```

### 验证部署

```bash
# 检查服务是否正常运行
curl http://localhost:8001/docs

# 或者在浏览器访问
# http://your-server-ip:8001/docs
```

---

## 详细部署步骤

### 步骤 1: 准备服务器环境

#### 1.1 更新系统

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 1.2 配置防火墙

```bash
# 开放 8001 端口（API 服务）
sudo ufw allow 8001/tcp

# 或者使用 firewalld (CentOS)
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload
```

#### 1.3 创建工作目录

```bash
# 创建应用目录
sudo mkdir -p /opt/its_knowledge
cd /opt/its_knowledge
```

### 步骤 2: 上传项目文件

有两种方式将项目文件传输到服务器：

#### 方式 1: 使用 Git（推荐）

```bash
# 克隆仓库
git clone https://github.com/deyongTang/its_multi_agent.git .

# 进入 knowledge 目录
cd backend/knowledge
```

#### 方式 2: 使用 SCP 上传

```bash
# 在本地机器执行
cd /Users/deyong/唐德勇/尚硅谷/ITS多智能体/代码/its_multi_agent
scp -r backend/knowledge user@your-server-ip:/opt/its_knowledge/
```

### 步骤 3: 配置环境变量

```bash
# 进入项目目录
cd /opt/its_knowledge/backend/knowledge

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env  # 或使用 vim
```

**重要配置项说明：**

```bash
# OpenAI API 配置（必填）
API_KEY=sk-xxxxxxxxxxxxx  # 你的 API Key
BASE_URL=https://api.openai.com/v1  # API 地址
MODEL=gpt-4  # 使用的模型
EMBEDDING_MODEL=text-embedding-3-small  # 向量化模型

# 数据库配置（如果使用 MySQL）
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-secure-password
DB_NAME=its_knowledge

# Elasticsearch 配置（必填）
ES_HOST=YOUR_SERVER_IP
ES_PORT=9200
ES_USERNAME=elastic
ES_PASSWORD=your-es-password
ES_INDEX_NAME=knowledge_index

# MinIO 配置（必填）
MINIO_ENDPOINT=YOUR_SERVER_IP:9000
MINIO_ACCESS_KEY=its_appkey
MINIO_SECRET_KEY=REDACTED_SECRET
MINIO_BUCKET=knowledge-base
```

### 步骤 4: 构建 Docker 镜像

```bash
# 构建镜像（首次构建可能需要 5-10 分钟）
docker compose build

# 查看构建的镜像
docker images | grep knowledge
```

### 步骤 5: 启动服务

```bash
# 启动服务（后台运行）
docker compose up -d

# 查看容器状态
docker compose ps

# 查看实时日志
docker compose logs -f knowledge-api
```

**预期输出：**

```text
✅ 日志系统已初始化（含 ES 输出）
✅ 环境变量已统一加载
🚀 准备启动 Web 服务器
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 步骤 6: 验证部署

```bash
# 测试 API 健康检查
curl http://localhost:8001/docs

# 测试文件上传接口
curl -X POST "http://localhost:8001/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.txt"

# 测试查询接口
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "测试问题"}'
```

---

## 配置说明

### 环境变量详解

#### OpenAI API 配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `API_KEY` | OpenAI API 密钥 | `sk-xxxxx` | ✅ |
| `BASE_URL` | API 基础地址 | `https://api.openai.com/v1` | ✅ |
| `MODEL` | 对话模型 | `gpt-4` | ✅ |
| `EMBEDDING_MODEL` | 向量化模型 | `text-embedding-3-small` | ✅ |

#### 数据库配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `DB_HOST` | MySQL 主机地址 | `localhost` | ❌ |
| `DB_PORT` | MySQL 端口 | `3306` | ❌ |
| `DB_USER` | 数据库用户名 | `root` | ❌ |
| `DB_PASSWORD` | 数据库密码 | `password` | ❌ |
| `DB_NAME` | 数据库名称 | `its_knowledge` | ❌ |

#### Elasticsearch 配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `ES_HOST` | ES 主机地址 | `YOUR_SERVER_IP` | ✅ |
| `ES_PORT` | ES 端口 | `9200` | ✅ |
| `ES_USERNAME` | ES 用户名 | `elastic` | ✅ |
| `ES_PASSWORD` | ES 密码 | `password` | ✅ |
| `ES_INDEX_NAME` | 索引名称 | `knowledge_index` | ✅ |

#### MinIO 配置

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `MINIO_ENDPOINT` | MinIO 地址 | `YOUR_SERVER_IP:9000` | ✅ |
| `MINIO_ACCESS_KEY` | 访问密钥 | `its_appkey` | ✅ |
| `MINIO_SECRET_KEY` | 密钥 | `REDACTED_SECRET` | ✅ |
| `MINIO_BUCKET` | 存储桶名称 | `knowledge-base` | ✅ |

#### RAG 配置

| 变量名 | 说明 | 默认值 | 说明 |
|--------|------|--------|------|
| `CHUNK_SIZE` | 文档切分大小 | `3000` | 字符数 |
| `CHUNK_OVERLAP` | 切分重叠大小 | `200` | 字符数 |
| `TOP_ROUGH` | 初始检索数量 | `50` | 文档数 |
| `TOP_FINAL` | 最终返回数量 | `5` | 文档数 |

### 端口配置

默认情况下，服务监听 `8001` 端口。如需修改：

1. 编辑 [docker-compose.yml](docker-compose.yml:9)
2. 修改 `ports` 配置：`"8080:8001"` (外部端口:内部端口)
3. 重启服务：`docker compose up -d`

### 数据持久化

以下目录会被挂载到宿主机，确保数据持久化：

- `./chroma_kb` - 向量数据库存储
- `./logs` - 应用日志
- `./data` - 上传的文档和爬取的数据

---

## 常见问题

### 1. 容器无法启动

**问题**: 运行 `docker compose up -d` 后容器立即退出

**解决方案**:

```bash
# 查看容器日志
docker compose logs knowledge-api

# 常见原因：
# 1. 环境变量未配置
# 2. 端口被占用
# 3. 依赖服务（ES/MinIO）无法连接
```

### 2. API Key 错误

**问题**: 日志显示 "Invalid API Key" 或 401 错误

**解决方案**:

```bash
# 检查 .env 文件中的 API_KEY 是否正确
cat .env | grep API_KEY

# 确保没有多余的空格或引号
# 正确格式: API_KEY=sk-xxxxx
# 错误格式: API_KEY="sk-xxxxx" 或 API_KEY= sk-xxxxx
```

### 3. Elasticsearch 连接失败

**问题**: 日志显示 "ES 客户端初始化失败"

**解决方案**:

```bash
# 测试 ES 连接
curl -u elastic:your_password http://YOUR_SERVER_IP:9200

# 检查防火墙是否开放 9200 端口
# 确认 ES_HOST、ES_USERNAME、ES_PASSWORD 配置正确
```

### 4. MinIO 连接失败

**问题**: 文件上传失败，日志显示 MinIO 错误

**解决方案**:

```bash
# 测试 MinIO 连接
curl http://YOUR_SERVER_IP:9000/minio/health/live

# 检查 MINIO_ENDPOINT、MINIO_ACCESS_KEY、MINIO_SECRET_KEY
# 确保 bucket 已创建
```

### 5. 端口被占用

**问题**: 启动时提示 "port is already allocated"

**解决方案**:

```bash
# 查看占用 8001 端口的进程
lsof -i :8001

# 停止占用端口的进程
kill -9 <PID>

# 或修改 docker-compose.yml 使用其他端口
# ports: "8080:8001"
```

### 6. 向量数据库损坏

**问题**: 查询时报错 "ChromaDB error"

**解决方案**:

```bash
# 停止服务
docker compose down

# 备份现有数据
mv chroma_kb chroma_kb.backup

# 重新创建向量库
mkdir chroma_kb

# 重新启动服务
docker compose up -d

# 重新上传文档
```

---

## 维护与监控

### 日常运维命令

#### 查看服务状态

```bash
# 查看所有容器状态
docker compose ps

# 查看容器资源使用情况
docker stats its-knowledge-api

# 查看容器详细信息
docker inspect its-knowledge-api
```

#### 日志管理

```bash
# 查看实时日志
docker compose logs -f knowledge-api

# 查看最近 100 行日志
docker compose logs --tail=100 knowledge-api

# 查看特定时间段的日志
docker compose logs --since="2024-01-01T00:00:00" knowledge-api

# 导出日志到文件
docker compose logs knowledge-api > logs_$(date +%Y%m%d).txt
```

#### 服务重启

```bash
# 重启服务（不重新构建）
docker compose restart

# 停止服务
docker compose stop

# 启动服务
docker compose start

# 完全停止并删除容器
docker compose down

# 重新构建并启动
docker compose up -d --build
```

### 更新部署

#### 更新代码

```bash
# 进入项目目录
cd /opt/its_knowledge/backend/knowledge

# 拉取最新代码
git pull origin main

# 重新构建镜像
docker compose build

# 重启服务
docker compose up -d
```

#### 更新依赖

```bash
# 如果 requirements.txt 有更新
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 备份与恢复

#### 备份数据

```bash
# 创建备份目录
mkdir -p /backup/knowledge_$(date +%Y%m%d)

# 备份向量数据库
tar -czf /backup/knowledge_$(date +%Y%m%d)/chroma_kb.tar.gz chroma_kb/

# 备份日志
tar -czf /backup/knowledge_$(date +%Y%m%d)/logs.tar.gz logs/

# 备份配置文件
cp .env /backup/knowledge_$(date +%Y%m%d)/
```

#### 恢复数据

```bash
# 停止服务
docker compose down

# 恢复向量数据库
tar -xzf /backup/knowledge_20240101/chroma_kb.tar.gz

# 恢复配置
cp /backup/knowledge_20240101/.env .

# 重启服务
docker compose up -d
```

### 性能优化

#### 资源限制

编辑 [docker-compose.yml](docker-compose.yml) 添加资源限制：

```yaml
services:
  knowledge-api:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### 日志轮转

```bash
# 配置 Docker 日志驱动
# 编辑 /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# 重启 Docker 服务
sudo systemctl restart docker
```

### 监控指标

#### 健康检查

```bash
# API 健康检查
curl http://localhost:8001/docs

# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' its-knowledge-api
```

#### 性能监控

```bash
# 实时监控容器资源使用
docker stats its-knowledge-api

# 查看容器进程
docker top its-knowledge-api
```

### 安全建议

#### 1. 环境变量安全

```bash
# 确保 .env 文件权限正确
chmod 600 .env

# 不要将 .env 文件提交到 Git
echo ".env" >> .gitignore
```

#### 2. 网络安全

```bash
# 使用防火墙限制访问
sudo ufw allow from 特定IP地址 to any port 8001

# 或使用 Nginx 反向代理并配置 SSL
```

#### 3. 定期更新

```bash
# 定期更新 Docker 镜像
docker compose pull
docker compose up -d

# 定期更新系统
sudo apt-get update && sudo apt-get upgrade -y
```

---

## 附录

### 完整部署脚本

创建一键部署脚本 `deploy.sh`：

```bash
#!/bin/bash
set -e

echo "🚀 开始部署 ITS Knowledge 知识库平台..."

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 2. 检查配置文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，从模板复制..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置必要的环境变量"
    exit 1
fi

# 3. 创建必要目录
mkdir -p chroma_kb logs data/oss data/crawl

# 4. 构建镜像
echo "📦 构建 Docker 镜像..."
docker compose build

# 5. 启动服务
echo "🚀 启动服务..."
docker compose up -d

# 6. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 7. 检查服务状态
if docker compose ps | grep -q "Up"; then
    echo "✅ 部署成功！"
    echo "📝 API 文档: http://localhost:8001/docs"
    echo "📊 查看日志: docker compose logs -f"
else
    echo "❌ 部署失败，请查看日志"
    docker compose logs
    exit 1
fi
```

使用方法：

```bash
# 赋予执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 卸载指南

```bash
# 停止并删除容器
docker compose down

# 删除镜像
docker rmi $(docker images | grep knowledge | awk '{print $3}')

# 删除数据（谨慎操作）
rm -rf chroma_kb logs data

# 删除配置
rm .env
```

---

## 技术支持

如遇到问题，请：

1. 查看日志：`docker compose logs -f knowledge-api`
2. 检查配置：确保 `.env` 文件配置正确
3. 查看文档：参考 [CLAUDE.md](../../CLAUDE.md) 了解项目架构
4. 提交 Issue：在项目仓库提交问题报告

---

## 部署架构说明

### 部署脚本职责划分

本项目采用**职责分离**的部署架构设计：

#### 1. GitHub Actions (`.github/workflows/deploy-knowledge.yml`)

**职责**: 仅负责触发部署，不包含具体部署逻辑

```yaml
# 只做三件事：
# 1. 连接到远程服务器
# 2. 执行项目中的部署脚本
# 3. 返回执行结果
```

**优势**:
- 配置简洁，只需维护服务器连接信息
- 部署逻辑在项目代码中，便于版本控制和测试
- 可以在本地直接运行部署脚本，无需依赖 CI/CD

#### 2. 部署脚本

**deploy.sh** - 本地/首次部署脚本
- 检查 Docker 环境
- 检查并创建 `.env` 配置文件
- 创建必要目录
- 构建镜像并启动服务
- 适用场景：开发环境、首次部署

**deploy-auto.sh** - 自动化部署脚本
- 检查并准备项目目录
- 拉取最新代码
- 停止旧容器
- 构建新镜像
- 启动新容器
- 验证部署状态
- 适用场景：生产环境、CI/CD 自动部署

### GitHub Actions 配置要求

在 GitHub 仓库的 Settings → Secrets 中配置以下密钥：

| 密钥名称 | 说明 | 示例值 |
|---------|------|--------|
| `SERVER_HOST` | 服务器 IP 地址 | `10.206.0.15` |
| `SERVER_USER` | SSH 用户名 | `root` |
| `SERVER_SSH_KEY` | SSH 私钥 | `-----BEGIN RSA PRIVATE KEY-----...` |
| `SERVER_PORT` | SSH 端口 | `22` |

### 触发部署的方式

**方式 1: 手动触发**
```bash
# 在 GitHub 仓库页面
Actions → Deploy Knowledge Platform → Run workflow
```

**方式 2: 自动触发**
```bash
# 推送代码到 main 分支的 backend/knowledge/ 目录
git add backend/knowledge/
git commit -m "update knowledge platform"
git push origin main
```

**方式 3: 直接在服务器执行**
```bash
# SSH 登录到服务器
ssh user@your-server-ip

# 执行部署脚本
cd /opt/its_multi_agent/backend/knowledge
bash deploy-auto.sh
```

### 部署流程图

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│  (只负责连接服务器并触发脚本)                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ SSH 连接
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   远程服务器                                  │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  deploy-auto.sh (项目中的部署脚本)                  │     │
│  │                                                   │     │
│  │  1. 检查环境 (Docker, docker-compose)              │     │
│  │  2. 准备项目目录 (/opt/its_multi_agent)            │     │
│  │  3. 拉取最新代码 (git pull)                        │     │
│  │  4. 停止旧容器 (docker-compose down)               │     │
│  │  5. 构建新镜像 (docker-compose build)              │     │
│  │  6. 启动新容器 (docker-compose up -d)              │     │
│  │  7. 验证部署 (docker-compose ps)                   │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions 自动化部署问题排查日志

### 部署日期
2026-01-27

### 部署环境
- **服务器地址**: 10.206.0.15
- **部署路径**: /opt/its_multi_agent
- **容器端口**: 8001
- **Docker Compose 版本**: docker-compose (旧版命令)

---

### 问题 1: MinIO 配置项缺失

**问题描述**: 在 `.test-env` 配置文件中缺少 MinIO 对象存储的配置项。

**错误现象**: 配置文件中只有 API、数据库和 Elasticsearch 配置，缺少 MinIO 相关配置。

**解决方案**: 在 `.test-env` 文件中添加 MinIO 配置：

```env
# minio 对象存储配置
MINIO_ENDPOINT=10.206.0.15:9000
MINIO_ACCESS_KEY=its_appkey
MINIO_SECRET_KEY=REDACTED_SECRET
MINIO_BUCKET=knowledge-base
MINIO_SECURE=false
```

**相关文件**:
- `backend/knowledge/.test-env`
- `backend/knowledge/config/settings.py` (第 30-35 行定义了 MinIO 配置项)

---

### 问题 2: GitHub Actions 部署脚本路径错误

**问题描述**: 部署脚本中使用的项目路径 `/opt/its_knowledge` 与实际仓库名不匹配。

**错误现象**:
```
bash: line 3: cd: backend/knowledge: No such file or directory
```

**根本原因**:
- 脚本中使用: `/opt/its_knowledge`
- 实际仓库名: `its_multi_agent`

**解决方案**: 修改 `.github/workflows/deploy-knowledge.yml` 中的路径为 `/opt/its_multi_agent`

**相关文件**: `.github/workflows/deploy-knowledge.yml`

---

### 问题 3: Docker Compose 命令版本不兼容

**问题描述**: 服务器上的 Docker 版本较旧，不支持 `docker compose` 命令（新版语法）。

**错误现象**:
```
docker: unknown command: docker compose
Run 'docker --help' for more information
```

**根本原因**:
- 新版 Docker: `docker compose` (子命令)
- 旧版 Docker: `docker-compose` (独立命令)

**解决方案**: 将所有 `docker compose` 改为 `docker-compose`

**相关文件**: `.github/workflows/deploy-knowledge.yml`

---

### 问题 4: Git 仓库认证失败

**问题描述**: 服务器通过 HTTPS 克隆 GitHub 仓库时需要交互式输入用户名密码。

**错误现象**:
```
fatal: could not read Username for 'https://github.com': No such device or address
```

**根本原因**: HTTPS 克隆需要认证，但 SSH 环境无法交互式输入凭据。

**解决方案**: 使用 GitHub Personal Access Token 进行认证：

```bash
git clone https://${GH_TOKEN}@github.com/deyongTang/its_multi_agent.git
```

**配置步骤**:
1. 访问 https://github.com/settings/tokens
2. 生成 Personal Access Token (勾选 `repo` 权限)
3. 在 GitHub 仓库 Settings → Secrets 中添加 `GH_TOKEN`

**相关文件**: `.github/workflows/deploy-knowledge.yml`

---

### 问题 5: 服务器目录存在但不是 Git 仓库

**问题描述**: `/opt/its_multi_agent` 目录存在，但不是有效的 Git 仓库。

**错误现象**:

```text
fatal: not a git repository (or any of the parent directories): .git
```

**根本原因**: 目录可能是手动创建的，或之前的部署失败导致 `.git` 目录缺失。

**解决方案**: 添加 Git 仓库检测逻辑：

```bash
if [ -d /opt/its_multi_agent ]; then
  cd /opt/its_multi_agent
  if [ ! -d .git ]; then
    echo "不是 Git 仓库，删除并重新克隆..."
    cd /opt
    rm -rf its_multi_agent
    git clone https://${GH_TOKEN}@github.com/deyongTang/its_multi_agent.git
  fi
fi
```

**相关文件**: `.github/workflows/deploy-knowledge.yml` (第 31-44 行)

---

### 问题 6: Docker Hub 镜像拉取失败

**问题描述**: 服务器无法访问 Docker Hub (`registry-1.docker.io`)，导致无法拉取基础镜像。

**错误现象**:

```text
Get "https://registry-1.docker.io/v2/": net/http: request canceled while waiting for connection
```

**根本原因**: 国内网络环境无法直接访问 Docker Hub。

**解决方案 1**: 配置 Docker 镜像加速

在 `/etc/docker/daemon.json` 中配置国内镜像源：

```json
{
  "registry-mirrors": [
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.nju.edu.cn"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

配置后重启 Docker:

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

**解决方案 2**: 配置 pip 国内镜像源

在 `Dockerfile` 中添加清华大学 pip 镜像：

```dockerfile
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**相关文件**:
- `.github/workflows/deploy-knowledge.yml` (第 59-84 行)
- `backend/knowledge/Dockerfile` (第 13-14 行)

---

### 问题 7: docker-compose.yml 环境变量配置冲突

**问题描述**: `docker-compose.yml` 中同时使用 `env_file` 和 `environment`，导致变量未设置警告。

**错误现象**:

```text
The MINIO_ENDPOINT variable is not set. Defaulting to a blank string.
The MINIO_ACCESS_KEY variable is not set. Defaulting to a blank string.
```

**根本原因**: 配置冲突：
- `env_file: .test-env` - 从文件读取变量（容器内生效）
- `environment: ${MINIO_ENDPOINT}` - 从 shell 环境读取（宿主机环境中不存在）

**解决方案**: 移除 `environment` 部分，只保留 `env_file`:

```yaml
services:
  knowledge-api:
    env_file:
      - .test-env
    # 移除 environment 部分
```

**相关文件**: `backend/knowledge/docker-compose.yml`

---

**部署完成！祝使用愉快！** 🎉
