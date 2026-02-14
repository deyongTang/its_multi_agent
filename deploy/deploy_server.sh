#!/bin/bash
# 一键部署和修复脚本
# 在服务器上运行此脚本即可完成所有配置

set -e

echo "=========================================="
echo "ITS 知识库平台 - 一键部署脚本"
echo "=========================================="

# 1. 修复数据库密码
echo ""
echo ">>> 步骤 1: 修复数据库用户密码..."
cd /path/to/its_multi_agent/backend/knowledge
python3 fix_password.py

# 2. 重启后端服务（如果需要）
echo ""
echo ">>> 步骤 2: 检查后端服务..."
if pgrep -f "python.*main.py" > /dev/null; then
    echo "后端服务正在运行"
else
    echo "启动后端服务..."
    nohup python3 presentation/api/main.py > ../../logs/knowledge.log 2>&1 &
    echo "✓ 后端服务已启动"
fi

echo ""
echo "=========================================="
echo "✓ 部署完成！"
echo "=========================================="
echo ""
echo "现在可以登录了:"
echo "  URL: http://118.195.198.38/login"
echo "  用户名: deyong"
echo "  密码: tang@4896"
