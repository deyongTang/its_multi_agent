#!/bin/bash
# GitHub Actions 自动部署脚本

set -e

echo "🚀 开始部署 ITS Knowledge 知识库平台..."

# 进入项目目录
cd /opt/its_knowledge

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 进入 knowledge 目录
cd backend/knowledge

# 停止旧容器
echo "🛑 停止旧容器..."
docker compose down

# 构建新镜像
echo "🔨 构建 Docker 镜像..."
docker compose build --no-cache

# 启动新容器
echo "🚀 启动新容器..."
docker compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "✅ 检查服务状态..."
docker compose ps

# 检查服务健康
if curl -f http://localhost:8001/docs > /dev/null 2>&1; then
    echo "✅ 部署成功！服务正常运行"
else
    echo "❌ 部署失败！服务未正常启动"
    docker compose logs --tail=50
    exit 1
fi
