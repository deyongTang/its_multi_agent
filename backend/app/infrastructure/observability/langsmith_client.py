"""
LangSmith 客户端封装模块 (LangGraph 版本)

LangGraph 会自动检测环境变量并启用追踪，无需额外配置
只需要设置以下环境变量：
- LANGCHAIN_TRACING_V2=true
- LANGCHAIN_API_KEY=your_api_key
- LANGCHAIN_PROJECT=your_project_name
- LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
"""
import os


class LangSmithClient:
    """
    LangSmith 客户端管理类

    仅用于初始化环境变量，LangGraph 会自动处理追踪
    """
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """
        初始化 LangSmith 环境变量

        从 settings 读取配置并设置到环境变量中
        LangGraph 会自动检测这些环境变量并启用追踪
        """
        if cls._initialized:
            return

        from infrastructure.logging.logger import logger

        try:
            from config.settings import settings

            # 只有在启用追踪且有 API Key 时才设置环境变量
            if not settings.LANGCHAIN_TRACING_V2 or not settings.LANGCHAIN_API_KEY:
                logger.info("LangSmith 追踪未启用")
                cls._initialized = True
                return

            # 设置环境变量（LangGraph 会自动检测）
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT or "ITS-MultiAgent"
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT or "https://api.smith.langchain.com"

            logger.info(f"✅ LangSmith 追踪已启用，项目: {os.environ['LANGCHAIN_PROJECT']}")
            cls._initialized = True

        except Exception as e:
            logger.error(f"❌ LangSmith 初始化失败: {e}")
            cls._initialized = True

    @classmethod
    def is_enabled(cls) -> bool:
        """检查 LangSmith 是否已启用"""
        return os.environ.get("LANGCHAIN_TRACING_V2") == "true"


# 全局客户端实例
langsmith_client = LangSmithClient
