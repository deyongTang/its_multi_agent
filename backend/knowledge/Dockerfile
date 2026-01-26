# 使用官方 Python 3.11 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（用于某些 Python 包的编译）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码到容器
COPY . .

# 创建必要的目录
RUN mkdir -p /app/logs \
    /app/chroma_kb \
    /app/data/oss \
    /app/data/crawl

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["python", "api/main.py"]
