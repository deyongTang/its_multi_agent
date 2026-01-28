"""
LangSmith 追踪功能测试脚本

用于验证 LangSmith 是否正确配置并能够追踪 Agent 执行
"""
import asyncio
from agents import Agent, Runner, function_tool, set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from config.settings import settings
from infrastructure.logging.logger import logger


@function_tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    return f"{city}的天气总是晴朗的！"


async def test_langsmith_tracing():
    """
    测试 LangSmith 追踪功能

    这个简单的测试会创建一个 Agent 并执行一个查询，
    如果 LangSmith 配置正确，你应该能在 LangSmith 平台看到追踪记录
    """
    logger.info("开始测试 LangSmith 追踪功能...")

    # 检查配置
    if not settings.LANGCHAIN_TRACING_V2:
        logger.warning("LangSmith 追踪未启用，请在 .env 中设置 LANGCHAIN_TRACING_V2=true")
        return

    if not settings.LANGCHAIN_API_KEY:
        logger.warning("LangSmith API Key 未配置")
        return

    logger.info(f"LangSmith 配置:")
    logger.info(f"  - 项目: {settings.LANGCHAIN_PROJECT}")
    logger.info(f"  - 端点: {settings.LANGCHAIN_ENDPOINT}")

    # 设置 trace processor
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    logger.info("Trace processor 已设置")

    # 创建测试 Agent
    agent = Agent(
        name="Weather Agent",
        instructions="你是一个有帮助的天气助手。",
        tools=[get_weather],
    )
    logger.info("测试 Agent 已创建")

    # 执行查询
    question = "北京的天气怎么样？"
    logger.info(f"执行查询: {question}")

    try:
        result = await Runner.run(agent, question)
        logger.info(f"查询结果: {result.final_output}")
        logger.info("✅ 测试成功！请前往 LangSmith 平台查看追踪记录")
        logger.info(f"   访问: https://smith.langchain.com/o/default/projects/p/{settings.LANGCHAIN_PROJECT}")
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_langsmith_tracing())

