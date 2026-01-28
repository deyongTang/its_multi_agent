from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from config.settings import settings
from typing import Any, Optional
import inspect

# 硅基流动配置(主模型)
SF_API_KEY = settings.SF_API_KEY
SF_BASE_URL = settings.SF_BASE_URL
MAIN_MODEL_NAME = settings.MAIN_MODEL_NAME

# 阿里百炼配置(子模型)
AL_BAILIAN_API_KEY = settings.AL_BAILIAN_API_KEY
AL_BAILIAN_BASE_URL = settings.AL_BAILIAN_BASE_URL
SUB_MODEL_NAME = settings.SUB_MODEL_NAME


# 模型名称映射：将带斜杠的模型名转换为 LangSmith 友好的格式
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


# 创建模型客户端（使用自定义包装器）
# 主模型客户端(协调Agent使用)
main_model_client = ModelNameMappingClient(
    original_model_name=MAIN_MODEL_NAME,
    base_url=SF_BASE_URL,
    api_key=SF_API_KEY
)

# 子模型客户端(干活的子Agent使用)
sub_model_client = ModelNameMappingClient(
    original_model_name=SUB_MODEL_NAME,
    base_url=AL_BAILIAN_BASE_URL,
    api_key=AL_BAILIAN_API_KEY
)


# 创建主调度模型
# 使用标准化的模型名称（LangSmith 友好），实际请求时会被包装器替换为原始名称
main_model = OpenAIChatCompletionsModel(
    model=normalize_model_name(MAIN_MODEL_NAME),  # LangSmith 看到: qwen3-32b
    openai_client=main_model_client
)

# 创建子调度模型
sub_model = OpenAIChatCompletionsModel(
    model=normalize_model_name(SUB_MODEL_NAME),  # LangSmith 看到: qwen3-max
    openai_client=sub_model_client
)
