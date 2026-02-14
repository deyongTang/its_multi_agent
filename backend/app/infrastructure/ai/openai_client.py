"""
OpenAI 客户端封装模块（双引擎版本）

同时提供两套模型客户端：
1. LangChain 模型 - 用于 LangGraph 工作流
2. OpenAI Agents SDK 模型 - 用于旧版 Orchestrator Agent

两者互不影响，各自提供服务
"""
from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI
from config.settings import settings

# ==================== 配置信息 ====================

# 硅基流动配置(主模型)
SF_API_KEY = settings.SF_API_KEY
SF_BASE_URL = settings.SF_BASE_URL
MAIN_MODEL_NAME = settings.MAIN_MODEL_NAME

# 阿里百炼配置(子模型)
AL_BAILIAN_API_KEY = settings.AL_BAILIAN_API_KEY
AL_BAILIAN_BASE_URL = settings.AL_BAILIAN_BASE_URL
SUB_MODEL_NAME = settings.SUB_MODEL_NAME


# ==================== 工具函数 ====================

def normalize_model_name(model_name: str) -> str:
    """
    将模型名称标准化为 LangSmith 可识别的格式
    例如: Qwen/Qwen3-32B -> qwen3-32b
    """
    if not model_name:
        return model_name
    # 移除前缀（斜杠之前的部分）
    if "/" in model_name:
        model_name = model_name.split("/")[-1]
    # 转换为小写
    return model_name.lower()


class ModelNameMappingClient(AsyncOpenAI):
    """
    自定义 AsyncOpenAI 客户端，在发送请求时将标准化的模型名映射回原始名称
    这样 LangSmith 看到的是标准化名称（qwen3-32b），但 API 收到的是原始名称（Qwen/Qwen3-32B）
    """
    def __init__(self, original_model_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_model_name = original_model_name
        self._normalized_model_name = normalize_model_name(original_model_name)

        # 包装 chat.completions.create 方法（OpenAI Agents SDK 使用这个）
        original_chat_create = self.chat.completions.create

        async def wrapped_chat_create(*args, **kwargs):
            # 如果请求中的 model 是标准化名称，替换为原始名称
            if 'model' in kwargs and kwargs['model'] == self._normalized_model_name:
                kwargs['model'] = self._original_model_name
            return await original_chat_create(*args, **kwargs)

        self.chat.completions.create = wrapped_chat_create


# ==================== OpenAI Agents SDK 模型（用于旧版 Orchestrator） ====================

# 创建模型客户端（使用自定义包装器）
# 主模型客户端(协调Agent使用)
agents_main_model_client = ModelNameMappingClient(
    original_model_name=MAIN_MODEL_NAME,
    base_url=SF_BASE_URL,
    api_key=SF_API_KEY
)

# 子模型客户端(干活的子Agent使用)
agents_sub_model_client = ModelNameMappingClient(
    original_model_name=SUB_MODEL_NAME,
    base_url=AL_BAILIAN_BASE_URL,
    api_key=AL_BAILIAN_API_KEY
)

# 创建主调度模型（OpenAI Agents SDK）
agents_main_model = OpenAIChatCompletionsModel(
    model=normalize_model_name(MAIN_MODEL_NAME),
    openai_client=agents_main_model_client
)

# 创建子调度模型（OpenAI Agents SDK）
agents_sub_model = OpenAIChatCompletionsModel(
    model=normalize_model_name(SUB_MODEL_NAME),
    openai_client=agents_sub_model_client
)


# ==================== LangChain 模型（用于 LangGraph 工作流） ====================

# 创建主模型（用于协调 Agent）
main_model = ChatOpenAI(
    model=MAIN_MODEL_NAME,
    openai_api_key=SF_API_KEY,
    openai_api_base=SF_BASE_URL,
    temperature=0.7,
    streaming=True,  # 支持流式输出
)

# 创建子模型（用于干活的子 Agent）
sub_model = ChatOpenAI(
    model=SUB_MODEL_NAME,
    openai_api_key=AL_BAILIAN_API_KEY,
    openai_api_base=AL_BAILIAN_BASE_URL,
    temperature=0.7,
    streaming=True,
)


# ==================== 导出说明 ====================
#
# 使用指南：
# 1. LangGraph 工作流使用：main_model, sub_model
# 2. OpenAI Agents SDK 使用：agents_main_model, agents_sub_model
#
# 示例：
#   from infrastructure.ai.openai_client import main_model  # LangGraph
#   from infrastructure.ai.openai_client import agents_main_model  # Agents SDK
