#!/bin/bash
# 前端构建脚本
# 使用方法：chmod +x build.sh && ./build.sh

set -e

echo "=========================================="
echo "开始构建知识库平台前端..."
echo "=========================================="

cd ../front/knowlege_platform_ui

echo ">>> 安装依赖..."
npm install

echo ">>> 开始构建..."
npm run build

echo ""
echo "=========================================="
echo "✓ 前端构建完成！"
echo "=========================================="
echo ""
echo "构建产物位置: front/knowlege_platform_ui/dist/"
