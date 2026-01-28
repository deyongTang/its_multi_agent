"""
LangSmith 连接诊断脚本

用于排查 LangSmith 配置和连接问题
"""
import os
import sys
import asyncio
from config.settings import settings
from infrastructure.logging.logger import logger


def check_environment_variables():
    """检查环境变量是否正确设置"""
    logger.info("=" * 60)
    logger.info("步骤 1: 检查环境变量")
    logger.info("=" * 60)

    env_vars = {
        "LANGCHAIN_TRACING_V2": os.environ.get("LANGCHAIN_TRACING_V2"),
        "LANGCHAIN_API_KEY": os.environ.get("LANGCHAIN_API_KEY"),
        "LANGCHAIN_PROJECT": os.environ.get("LANGCHAIN_PROJECT"),
        "LANGCHAIN_ENDPOINT": os.environ.get("LANGCHAIN_ENDPOINT"),
    }

    for key, value in env_vars.items():
        if value:
            if key == "LANGCHAIN_API_KEY":
                logger.info(f"✅ {key}: {value[:20]}...")
            else:
                logger.info(f"✅ {key}: {value}")
        else:
            logger.warning(f"❌ {key}: 未设置")

    return all(env_vars.values())


def check_settings():
    """检查 settings 配置"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 2: 检查 Settings 配置")
    logger.info("=" * 60)

    logger.info(f"LANGCHAIN_TRACING_V2: {settings.LANGCHAIN_TRACING_V2}")
    logger.info(f"LANGCHAIN_API_KEY: {settings.LANGCHAIN_API_KEY[:20] if settings.LANGCHAIN_API_KEY else 'None'}...")
    logger.info(f"LANGCHAIN_PROJECT: {settings.LANGCHAIN_PROJECT}")
    logger.info(f"LANGCHAIN_ENDPOINT: {settings.LANGCHAIN_ENDPOINT}")

    if not settings.LANGCHAIN_TRACING_V2:
        logger.error("❌ LANGCHAIN_TRACING_V2 未启用！")
        return False

    if not settings.LANGCHAIN_API_KEY:
        logger.error("❌ LANGCHAIN_API_KEY 未配置！")
        return False

    logger.info("✅ Settings 配置正确")
    return True


def check_langsmith_connection():
    """检查 LangSmith API 连接"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 3: 测试 LangSmith API 连接")
    logger.info("=" * 60)

    try:
        import httpx

        api_key = settings.LANGCHAIN_API_KEY
        endpoint = settings.LANGCHAIN_ENDPOINT

        # 测试 API 连接
        url = f"{endpoint}/info"
        headers = {"x-api-key": api_key}

        logger.info(f"正在连接: {url}")

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            logger.info(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                logger.info("✅ LangSmith API 连接成功！")
                return True
            else:
                logger.error(f"❌ LangSmith API 连接失败: {response.text}")
                return False

    except Exception as e:
        logger.error(f"❌ 连接测试失败: {str(e)}")
        return False


def check_trace_processor():
    """检查 trace processor 是否正确设置"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 4: 检查 Trace Processor")
    logger.info("=" * 60)

    try:
        from agents import set_trace_processors
        from langsmith.wrappers import OpenAIAgentsTracingProcessor

        # 设置 trace processor
        set_trace_processors([OpenAIAgentsTracingProcessor()])
        logger.info("✅ Trace Processor 设置成功")
        return True

    except Exception as e:
        logger.error(f"❌ Trace Processor 设置失败: {str(e)}")
        return False


async def test_simple_agent():
    """测试简单的 Agent 执行"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 5: 测试 Agent 执行并发送追踪")
    logger.info("=" * 60)

    try:
        from agents import Agent, Runner, function_tool
        from infrastructure.ai.openai_client import main_model, sub_model

        @function_tool
        def get_weather(city: str) -> str:
            """获取指定城市的天气"""
            return f"{city}的天气很好！"

        # 使用我们配置好的模型（已经处理了模型名称映射）
        if settings.SF_API_KEY and settings.SF_BASE_URL:
            model_to_use = main_model
            logger.info(f"使用硅基流动 API: {settings.SF_BASE_URL}")
            logger.info(f"模型名称: {main_model.model} (实际调用: {settings.MAIN_MODEL_NAME})")
        elif settings.AL_BAILIAN_API_KEY and settings.AL_BAILIAN_BASE_URL:
            model_to_use = sub_model
            logger.info(f"使用阿里百炼 API: {settings.AL_BAILIAN_BASE_URL}")
            logger.info(f"模型名称: {sub_model.model} (实际调用: {settings.SUB_MODEL_NAME})")
        else:
            logger.error("❌ 没有配置可用的 AI 服务")
            return False

        # 创建简单的 Agent（使用我们配置好的模型对象）
        agent = Agent(
            name="Test Agent",
            instructions="你是一个测试助手",
            tools=[get_weather],
            model=model_to_use,
        )

        logger.info("正在执行 Agent...")
        result = await Runner.run(agent, "北京天气怎么样？")

        logger.info(f"✅ Agent 执行成功！")
        logger.info(f"结果: {result.final_output}")
        logger.info("\n请等待 5-10 秒，然后检查 LangSmith 平台是否收到追踪数据")
        logger.info(f"访问: https://smith.langchain.com")

        return True

    except Exception as e:
        logger.error(f"❌ Agent 执行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """主诊断流程"""
    logger.info("\n" + "🔍 开始 LangSmith 连接诊断")
    logger.info("=" * 60)

    # 首先初始化 LangSmith 客户端（这会设置环境变量）
    logger.info("\n初始化 LangSmith 客户端...")
    from infrastructure.observability.langsmith_client import langsmith_client
    langsmith_client.initialize()

    # 步骤 1: 检查环境变量
    if not check_environment_variables():
        logger.error("\n❌ 环境变量检查失败，请检查 .env 文件")
        return

    # 步骤 2: 检查 Settings
    if not check_settings():
        logger.error("\n❌ Settings 配置检查失败")
        return

    # 步骤 3: 测试 API 连接
    if not check_langsmith_connection():
        logger.error("\n❌ LangSmith API 连接失败，请检查 API Key 是否正确")
        return

    # 步骤 4: 设置 Trace Processor
    if not check_trace_processor():
        logger.error("\n❌ Trace Processor 设置失败")
        return

    # 步骤 5: 测试 Agent 执行
    if not await test_simple_agent():
        logger.error("\n❌ Agent 执行失败")
        return

    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有诊断步骤完成！")
    logger.info("=" * 60)
    logger.info("\n如果 LangSmith 平台仍然没有显示追踪数据，可能的原因：")
    logger.info("1. 追踪数据需要几秒钟才能显示在平台上")
    logger.info("2. 检查项目名称是否正确")
    logger.info("3. 检查是否在正确的组织下查看")


if __name__ == "__main__":
    asyncio.run(main())




