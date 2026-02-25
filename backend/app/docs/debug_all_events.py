"""打印所有事件的 kind 和 name"""
import asyncio, sys
sys.path.insert(0, "/Users/deyong/唐德勇/尚硅谷/ITS多智能体/代码/its_multi_agent/backend/app")
from multi_agent.workflow.runner import WorkflowRunner

async def main():
    runner = WorkflowRunner()
    async for event in runner.stream_run(
        user_query="你好", user_id="debug", session_id="debug_all",
    ):
        kind = event.get("event", "")
        name = event.get("name", "")
        print(f"  {kind:30s} | {name}")

asyncio.run(main())
