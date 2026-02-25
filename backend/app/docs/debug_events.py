"""直接调用 WorkflowRunner 打印原始事件，绕过 SSE 层"""
import asyncio
import sys
import os

# 设置路径
sys.path.insert(0, "/Users/deyong/唐德勇/尚硅谷/ITS多智能体/代码/its_multi_agent/backend/app")

from multi_agent.workflow.runner import WorkflowRunner

async def main():
    runner = WorkflowRunner()

    print("开始流式运行...")
    count = 0
    async for event in runner.stream_run(
        user_query="你好",
        user_id="debug",
        session_id="debug_raw",
    ):
        count += 1
        kind = event.get("event", "")
        name = event.get("name", "")
        # 只打印关键事件
        if kind in ("on_node_start", "on_node_end",
                     "on_chat_model_stream", "on_chain_end",
                     "on_chain_start"):
            data_keys = list(event.get("data", {}).keys())
            print(f"  [{count}] {kind} | name={name} | data_keys={data_keys}")

    print(f"\n总事件数: {count}")

asyncio.run(main())
