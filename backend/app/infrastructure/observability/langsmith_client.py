"""
LangSmith 客户端封装模块

提供统一的 LangSmith 追踪功能，支持：
1. 环境变量配置管理
2. 追踪会话和智能体执行
3. 记录 LLM 调用和工具使用
4. 自动错误处理
"""
import os
from typing import Optional


class LangSmithClient:
    """
    LangSmith 客户端管理类

    通过环境变量配置 LangSmith 追踪功能
    """
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """
        初始化 LangSmith 客户端

        设置环境变量并配置 trace processor 以启用 LangSmith 追踪
        """
        # 延迟导入所有依赖，避免循环导入和初始化顺序问题
        from infrastructure.logging.logger import logger

        try:
            from config.settings import settings

            tracing_enabled = settings.LANGCHAIN_TRACING_V2
            api_key = settings.LANGCHAIN_API_KEY
            project = settings.LANGCHAIN_PROJECT
            endpoint = settings.LANGCHAIN_ENDPOINT
        except Exception as e:
            logger.error(f"无法加载 LangSmith 配置: {e}")
            return

        if not tracing_enabled:
            if not cls._initialized:
                logger.info("LangSmith 追踪未启用")
            cls._initialized = True
            return

        if not api_key:
            if not cls._initialized:
                logger.warning("LangSmith API Key 未配置，追踪功能将被禁用")
            cls._initialized = True
            return

        try:
            # 设置 LangSmith 环境变量 (如果是首次初始化)
            if not cls._initialized:
                os.environ["LANGCHAIN_TRACING_V2"] = str(tracing_enabled).lower()
                os.environ["LANGCHAIN_API_KEY"] = api_key

                if project:
                    os.environ["LANGCHAIN_PROJECT"] = project

                if endpoint:
                    os.environ["LANGCHAIN_ENDPOINT"] = endpoint

            # 设置 OpenAI Agents 的 trace processor
            # 注意：这步操作在每次 initialize 调用时都会执行，确保 Context 传递正确
            from agents import set_trace_processors
            from langsmith.wrappers import OpenAIAgentsTracingProcessor

            # 【关键补丁】防止 tracing processor 内部检查 OPENAI_API_KEY 导致静默失败
            if "OPENAI_API_KEY" not in os.environ:
                os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-tracing"

            set_trace_processors([OpenAIAgentsTracingProcessor()])

            if not cls._initialized:
                logger.info(f"LangSmith 客户端初始化成功，项目: {project}")
                cls._initialized = True

        except Exception as e:
            logger.error(f"LangSmith 客户端初始化失败: {str(e)}")
            cls._initialized = True

    @classmethod
    def is_enabled(cls) -> bool:
        """
        检查 LangSmith 是否已启用

        Returns:
            bool: 是否启用
        """
        try:
            from config.settings import settings
            return settings.LANGCHAIN_TRACING_V2 and bool(settings.LANGCHAIN_API_KEY)
        except:
            return False


# 全局客户端实例
langsmith_client = LangSmithClient
