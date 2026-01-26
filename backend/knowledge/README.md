# ITS Knowledge 知识库平台 - Docker 部署

## 快速部署指南

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/deyongTang/its_multi_agent.git
cd its_multi_agent/backend/knowledge

# 2. 配置环境变量
cp .env.example .env
vim .env  # 修改必填配置项

# 3. 一键部署
./deploy.sh
```

### 必填配置项

编辑 `.env` 文件，配置以下必填项：

```bash
# OpenAI API
API_KEY=your_openai_api_key
BASE_URL=https://api.openai.com/v1

# Elasticsearch
ES_HOST=your_es_host
ES_PASSWORD=your_es_password

# MinIO
MINIO_ENDPOINT=your_minio_endpoint
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
```

### 验证部署

```bash
# 查看服务状态
docker compose ps

# 访问 API 文档
curl http://localhost:8001/docs
```

### 常用命令

```bash
# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down
```

## 详细文档

完整的部署文档请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 项目架构

详细的项目架构说明请参考 [CLAUDE.md](../../CLAUDE.md)

## GitHub 仓库

https://github.com/deyongTang/its_multi_agent
