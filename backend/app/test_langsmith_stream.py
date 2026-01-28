import asyncio
import os
import sys
from config.settings import settings
from infrastructure.logging.logger import logger

# 1. Simulate main.py: Initialize LangSmith FIRST
from infrastructure.observability.langsmith_client import langsmith_client

logger.info("Initializing LangSmith...")
langsmith_client.initialize()

# 2. Simulate imports happening AFTER initialization
from agents import Runner
from multi_agent.orchestrator_agent import orchestrator_agent
from services.stream_response_service import process_stream_response

async def test_langsmith_tracing_exact_replica():
    logger.info("开始测试 LangSmith 追踪功能 (Exact Replica)...")

    # Construct input like agent_service
    user_query = "电脑蓝屏怎么办"
    chat_history = [{"role": "user", "content": user_query}]
    
    logger.info(f"执行查询: {user_query}")
    logger.info(f"Input type: {type(chat_history)}")

    try:
        # 3. Call exactly like agent_service
        streaming_result = Runner.run_streamed(
            starting_agent=orchestrator_agent,
            input=chat_history,
            context=user_query,
            max_turns=5,
        )
        
        # 4. Consume stream
        async for chunk in process_stream_response(streaming_result):
             pass # Just consume

        logger.info(f"查询结果: {streaming_result.final_output}")
        logger.info("✅ 测试成功！请检查 LangSmith 是否有 '主调度智能体' (Orchestrator Agent) 的记录")
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_langsmith_tracing_exact_replica())
