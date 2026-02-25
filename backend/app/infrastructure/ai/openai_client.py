"""
OpenAI 客户端封装模块

提供 LangChain 模型客户端，用于 LangGraph 工作流
"""
from langchain_openai import ChatOpenAI
from config.settings import settings

# ==================== 配置信息 ====================

SF_API_KEY = settings.SF_API_KEY
SF_BASE_URL = settings.SF_BASE_URL
MAIN_MODEL_NAME = settings.MAIN_MODEL_NAME

AL_BAILIAN_API_KEY = settings.AL_BAILIAN_API_KEY
AL_BAILIAN_BASE_URL = settings.AL_BAILIAN_BASE_URL
SUB_MODEL_NAME = settings.SUB_MODEL_NAME


# ==================== LangChain 模型（用于 LangGraph 工作流） ====================

main_model = ChatOpenAI(
    model=MAIN_MODEL_NAME,
    openai_api_key=SF_API_KEY,
    openai_api_base=SF_BASE_URL,
    temperature=0.7,
    streaming=True,
    model_kwargs={"extra_body": {"enable_thinking": False}},  # 禁用思维链，减少延迟

)

sub_model = ChatOpenAI(
    model=SUB_MODEL_NAME,
    openai_api_key=SF_API_KEY,
    openai_api_base=SF_BASE_URL,
    temperature=0.7,
    streaming=False,  # 结构化 JSON 提取不需要流式，避免截断
    model_kwargs={"extra_body": {"enable_thinking": False}},  # 禁用思维链，减少延迟
)
