import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

# 【关键修复】确保从正确的路径导入 settings
# 移除 backend/knowledge 路径，避免导入冲突
knowledge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../knowledge'))
if knowledge_path in sys.path:
    sys.path.remove(knowledge_path)

# 确保当前项目路径在搜索路径的最前面
current_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if current_app_path in sys.path:
    sys.path.remove(current_app_path)
sys.path.insert(0, current_app_path)

# 0. 最优先：确保 settings 在所有模块之前被正确加载
from config.settings import settings

from infrastructure.logging.logger import logger

# 提前导入所有需要 settings 的模块，确保它们在 lifespan 之前加载完成
from infrastructure.observability.langsmith_client import langsmith_client
from infrastructure.tools.mcp.mcp_manager import mcp_connect, mcp_cleanup
from infrastructure.middleware import TraceIdMiddleware

from api.routers import router

# Explicitly print to stdout to confirm this file is running
print(">>> Running Gemini Fixed Version of api/main.py <<<")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI应用生命周期管理

    所有需要 settings 的模块已在文件顶部导入，
    确保在 lifespan 事件执行时它们已经完全加载
    """
    # 应用启动时执行
    logger.info("应用启动，初始化服务...")

    # 1. 初始化 LangSmith
    try:
        langsmith_client.initialize()
        logger.info("LangSmith 初始化完成")
    except Exception as e:
        logger.error(f"LangSmith 初始化失败: {str(e)}")

    # 2. 建立 MCP 连接
    try:
        await mcp_connect()
        logger.info("MCP连接建立完成")
    except Exception as e:
        logger.error(f"MCP连接建立失败: {str(e)}")

    yield  # 应用运行期间

    # 应用关闭时执行
    logger.info("应用关闭，清理资源...")

    # 清理 MCP 连接
    try:
        await mcp_cleanup()
        logger.info("MCP连接清理完成")
    except Exception as e:
        logger.error(f"MCP连接清理失败: {str(e)}")


def create_fast_api() -> FastAPI:
    app = FastAPI(title="ITS API", lifespan=lifespan)

    # 1. 添加 TraceId 中间件（必须在 CORS 之前，确保每个请求都有 traceId）
    app.add_middleware(TraceIdMiddleware)

    # 2. 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router=router)
    return app


if __name__ == '__main__':
    import asyncio
    import sys
    
    print("1.准备启动Web服务器 (Manual Loop Mode)")
    try:
        # 使用 Server 对象直接启动，避免 uvicorn.run 在 Python 3.13+ 调用 asyncio.run 时传入不支持的 loop_factory 参数
        config = uvicorn.Config(app=create_fast_api(), host="127.0.0.1", port=8000)
        server = uvicorn.Server(config)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ensure we don't accidentally use the patched run
        print("2.正在启动事件循环...")
        loop.run_until_complete(server.serve())

        logger.info("3.启动Web服务器成功...")

    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        # Use a distinctive error message to trace if this block is hit
        logger.error(f"!!! CRITICAL STARTUP ERROR !!!: {str(e)}")
        import traceback
        traceback.print_exc()