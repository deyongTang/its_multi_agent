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
