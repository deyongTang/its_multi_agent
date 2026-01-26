#!/bin/bash
# 本地部署脚本
# 用途：在本地或首次部署时使用，会检查环境和配置文件

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 ITS Knowledge 知识库平台 - 本地部署"
echo "=========================================="

# ============================================
# 1. 环境检查
# ============================================
echo ""
echo "📋 步骤 1/6: 检查部署环境..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

# 检查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: docker-compose 未安装"
    echo "请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# ============================================
# 2. 检查配置文件
# ============================================
echo ""
echo "📋 步骤 2/6: 检查配置文件..."

if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在"

    if [ -f .env.example ]; then
        echo "📝 从模板复制 .env.example -> .env"
        cp .env.example .env
        echo ""
        echo "⚠️  请编辑 .env 文件配置以下必要的环境变量："
        echo "   - API_KEY: OpenAI API 密钥"
        echo "   - BASE_URL: API 地址"
        echo "   - ES_HOST, ES_PASSWORD: Elasticsearch 配置"
        echo "   - MINIO_ENDPOINT, MINIO_ACCESS_KEY: MinIO 配置"
        echo ""
        echo "配置完成后，请重新运行此脚本"
        exit 1
    else
        echo "❌ 错误: .env.example 模板文件不存在"
        exit 1
    fi
fi

echo "✅ 配置文件检查通过"

# ============================================
# 3. 创建必要目录
# ============================================
echo ""
echo "📂 步骤 3/6: 创建必要目录..."

mkdir -p chroma_kb logs data/oss data/crawl

echo "✅ 目录创建完成"
echo "   - chroma_kb/  (向量数据库)"
echo "   - logs/       (应用日志)"
echo "   - data/oss/   (上传文件)"
echo "   - data/crawl/ (爬取数据)"

# ============================================
# 4. 停止旧容器
# ============================================
echo ""
echo "🛑 步骤 4/6: 停止旧容器（如果存在）..."

docker-compose down || true
echo "✅ 旧容器已停止"

# ============================================
# 5. 构建镜像
# ============================================
echo ""
echo "🔨 步骤 5/6: 构建 Docker 镜像..."

docker-compose build
echo "✅ 镜像构建完成"

# ============================================
# 6. 启动服务
# ============================================
echo ""
echo "🚀 步骤 6/6: 启动服务..."

docker-compose up -d
echo "✅ 容器启动完成"

# ============================================
# 7. 验证部署
# ============================================
echo ""
echo "🔍 验证部署状态..."
echo ""

# 等待服务启动
sleep 5

# 显示容器状态
echo "📊 容器状态:"
docker-compose ps

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "📝 API 文档: http://localhost:8001/docs"
echo "📊 查看日志: docker-compose logs -f"
echo "🔍 检查状态: docker-compose ps"
echo "🛑 停止服务: docker-compose down"
echo ""
