"""打印 on_chain_start/end 的详细数据"""
import asyncio, sys, json
sys.path.insert(0, "/Users/deyong/唐德勇/尚硅谷/ITS多智能体/代码/its_multi_agent/backend/app")
from multi_agent.workflow.runner import WorkflowRunner

async def main():
    runner = WorkflowRunner()
    async for event in runner.stream_run(
        user_query="你好", user_id="debug", session_id="debug_detail",
    ):
        kind = event.get("event", "")
        name = event.get("name", "")
        data = event.get("data", {})
        metadata = event.get("metadata", {})

        if kind == "on_chain_start" and name not in ("LangGraph", "route_intent", "ChatOpenAI"):
            print(f"\n>>> {kind} | {name}")
            print(f"    metadata keys: {list(metadata.keys())}")
            lg_node = metadata.get("langgraph_node", "?")
            print(f"    langgraph_node: {lg_node}")

        elif kind == "on_chain_end" and name not in ("LangGraph", "route_intent", "ChatOpenAI"):
            print(f"\n>>> {kind} | {name}")
            output = data.get("output", {})
            if isinstance(output, dict):
                for k, v in output.items():
                    if k == "messages":
                        for m in v:
                            content = m.content if hasattr(m, "content") else str(m)
                            print(f"    messages: [{m.type}] {content[:80]}")
                    else:
                        print(f"    {k}: {str(v)[:80]}")
            else:
                print(f"    output type: {type(output).__name__}")

        elif kind == "on_chat_model_end":
            print(f"\n>>> {kind} | {name}")
            lg_node = metadata.get("langgraph_node", "?")
            print(f"    langgraph_node: {lg_node}")
            output = data.get("output", None)
            if output and hasattr(output, "content"):
                print(f"    content: {output.content[:80]}")

asyncio.run(main())
