from collections.abc import AsyncGenerator
from typing import Any
from utils.response_util import ResponseFactory
from schemas.response import ContentKind
from infrastructure.logging.logger import logger

# 只有这些节点的 LLM 输出才透传给前端作为最终答案
_ANSWER_NODES = {"generate_report", "general_chat", "ask_user"}

async def process_workflow_stream(workflow_stream: AsyncGenerator) -> AsyncGenerator:
    """
    处理 LangGraph 异步事件流并转换为前端 SSE 格式

    Args:
        workflow_stream: LangGraph astream_events 生成器
    """
    # 追踪当前正在执行的节点
    current_node: str = ""
    # 内部节点名称，不展示给前端
    _INTERNAL_NAMES = {"__start__", "__end__", "LangGraph"}
    # 条件路由函数名称，不作为节点展示
    _ROUTER_NAMES = {"route_intent", "route_slot_check", "route_verify_result",
                     "route_dispatch", "route_kb_check", "route_evaluate"}

    async for event in workflow_stream:
        kind = event.get("event")
        name = event.get("name")
        data = event.get("data")
        metadata = event.get("metadata", {})

        # ── 1. 节点开始 → PROCESS 提示 ──
        # astream_events v2 中节点事件为 on_chain_start/on_chain_end
        if kind == "on_chain_start":
            lg_node = metadata.get("langgraph_node", "")
            # 只处理 LangGraph 节点（有 langgraph_node 元数据），跳过内部和路由
            if lg_node and name == lg_node and name not in _INTERNAL_NAMES and name not in _ROUTER_NAMES:
                current_node = name
                yield "data: " + ResponseFactory.build_text(
                    f"🔄 进入环节: {name}", ContentKind.PROCESS
                ).model_dump_json() + "\n\n"

        # ── 2. 节点结束 → 提取答案节点的回复 ──
        elif kind == "on_chain_end":
            lg_node = metadata.get("langgraph_node", "")

            # 追问节点：从 output state 取出追问内容
            if name == "ask_user" and lg_node == "ask_user":
                output = data.get("output", {})
                messages = output.get("messages", [])
                pending_intent = output.get("current_intent", "")
                for msg in messages:
                    content = msg.content if hasattr(msg, "content") else str(msg)
                    if content:
                        import json as _json
                        packet = ResponseFactory.build_text(content, ContentKind.ANSWER).model_dump()
                        packet["is_ask_user"] = True
                        packet["pending_intent"] = pending_intent
                        yield "data: " + _json.dumps(packet, ensure_ascii=False) + "\n\n"

            # 其他答案节点（general_chat, generate_report）：从 output messages 提取回复
            elif name in _ANSWER_NODES and lg_node == name and name != "ask_user":
                output = data.get("output", {})
                messages = output.get("messages", [])
                for msg in messages:
                    content = msg.content if hasattr(msg, "content") else str(msg)
                    if content:
                        yield "data: " + ResponseFactory.build_text(
                            content, ContentKind.ANSWER
                        ).model_dump_json() + "\n\n"

            if lg_node and name == lg_node:
                current_node = ""

        # ── 3. LLM 流式输出（如果节点使用 astream 调用 LLM）──
        elif kind == "on_chat_model_stream":
            chunk = data.get("chunk", None)
            if not chunk:
                continue

            source_node = metadata.get("langgraph_node", current_node)

            # 提取推理内容 (Thinking)
            reasoning = None
            if hasattr(chunk, "reasoning_content") and chunk.reasoning_content:
                reasoning = chunk.reasoning_content
            elif hasattr(chunk, "additional_kwargs") and "reasoning_content" in chunk.additional_kwargs:
                reasoning = chunk.additional_kwargs["reasoning_content"]

            if reasoning:
                yield "data: " + ResponseFactory.build_text(
                    reasoning, ContentKind.THINKING
                ).model_dump_json() + "\n\n"

            # 流式答案（仅答案节点）
            content = chunk.content if hasattr(chunk, "content") else None
            if content and source_node in _ANSWER_NODES:
                yield "data: " + ResponseFactory.build_text(
                    content, ContentKind.ANSWER
                ).model_dump_json() + "\n\n"

        # ── 4. 工具调用 ──
        elif kind == "on_tool_start":
            yield "data: " + ResponseFactory.build_text(
                f"🔧 调用工具: {name}", ContentKind.PROCESS
            ).model_dump_json() + "\n\n"

        # ── 5. 自定义事件（预留扩展）──
        elif kind == "on_custom_event":
            pass

    # 5. 发送结束信号
    yield "data: " + ResponseFactory.build_finish().model_dump_json() + "\n\n"