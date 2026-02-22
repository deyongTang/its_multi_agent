#!/bin/bash

# ITS Multi-Agent 启动脚本
# 用途：清除代理环境变量，避免 MCP SSE 连接问题

echo "正在启动 ITS Multi-Agent 服务..."

# 清除代理环境变量（避免 MCP 客户端连接失败）
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy

echo "已清除代理环境变量"
echo "HTTP_PROXY: ${HTTP_PROXY:-未设置}"
echo "HTTPS_PROXY: ${HTTPS_PROXY:-未设置}"

# 切换到应用目录
cd "$(dirname "$0")"

# 启动 FastAPI 应用
echo "启动 FastAPI 服务器..."
python api/main.py
