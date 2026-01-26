"""

创建FastAPI实例 并且管理所有的路由

"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

# 使用新的日志系统
from infrastructure.logger import logger, setup_logger
from infrastructure.middleware import TraceIdMiddleware

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import router

# 全局标志，确保日志系统只初始化一次
_logger_initialized = False


def init_logger():
    """初始化日志系统（只执行一次）"""
    global _logger_initialized
    if not _logger_initialized:
        # 1. 初始化 ES 客户端
        es_instance = None
        try:
            from infrastructure.es_client import ESClient
            es_client = ESClient()
            es_instance = es_client.client
        except Exception as e:
            print(f"⚠️ ES 客户端初始化失败: {e}")

        # 2. 配置日志系统（启用 ES 输出）
        setup_logger(
            log_dir="./logs",
            log_level="INFO",
            rotation="00:00",
            retention="30 days",
            enable_json=False,
            enable_es=True,  # 启用 ES 日志
            es_client=es_instance,  # 传入 ES 客户端
            es_index_prefix="app-logs"  # 设置索引前缀
        )
        _logger_initialized = True
        logger.info("✅ 日志系统已初始化（含 ES 输出）")


def setup_environment():
    """
    统一设置环境变量
    在应用启动时调用一次，避免在各个模块中重复设置
    """
    os.environ["OPENAI_API_KEY"] = settings.API_KEY
    # 注意：langchain-openai 使用 OPENAI_BASE_URL 而不是 OPENAI_API_BASE
    os.environ["OPENAI_BASE_URL"] = settings.BASE_URL
    logger.info("✅ 环境变量已统一加载")


def create_fast_api() -> FastAPI:
    """创建并配置 FastAPI 应用"""

    # 0. 初始化日志系统（确保在任何启动方式下都能正确初始化）
    init_logger()

    # 1. 创建 FastAPI 实例
    app = FastAPI(title="Knowledge API")

    # 2. 添加 CORS 中间件（允许前端跨域请求）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源，生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )

    # 3. 添加 TraceId 中间件（必须在路由注册之前）
    app.add_middleware(TraceIdMiddleware)

    # 4. 注册各种路由
    app.include_router(router=router)

    # 5. 返回创建的 FastAPI
    return app



if __name__ == '__main__':
    # 日志系统会在 create_fast_api() 中自动初始化
    logger.info("🚀 准备启动 Web 服务器")

    # 统一设置环境变量
    setup_environment()

    try:
        # 启动 FastAPI 应用
        # 绑定 0.0.0.0 允许外部网络访问，127.0.0.1 仅允许本机访问
        uvicorn.run(
            app=create_fast_api(),
            host="0.0.0.0",
            port=8001,
            log_config=None  # 禁用 uvicorn 默认日志，使用我们的 loguru
        )
        logger.info("✅ Web 服务器启动成功")
    except KeyboardInterrupt:
        logger.warning("⚠️ 服务器被用户中断")
    except Exception as e:
        logger.error(f"❌ 启动 Web 服务器失败: {str(e)}")














