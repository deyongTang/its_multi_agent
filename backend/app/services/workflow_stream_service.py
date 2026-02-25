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
    # 追踪当前正在执行的节点（用于过滤 on_chat_model_stream 来源）
    current_node: str = ""

    async for event in workflow_stream:
        kind = event.get("event")
        name = event.get("name")
        data = event.get("data")

        # 1. 处理节点开始/结束事件 (PROCESS 类型)
        if kind == "on_chain_start" and name == "LangGraph":
             pass # 流程开始

        # 追问节点结束时，从 output state 取出追问内容发给前端
        elif kind == "on_chain_end" and name == "ask_user":
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

        elif kind == "on_node_start":
            node_name = name
            current_node = node_name
            # 过滤掉内部节点名称，只展示有意义的节点
            if node_name not in ["__start__", "__end__", "LangGraph"]:
                text = f"进入环节: {node_name}"
                yield "data: " + ResponseFactory.build_text(
                    f"🔄 {text}", ContentKind.PROCESS
                ).model_dump_json() + "\n\n"

        elif kind == "on_node_end":
            current_node = ""

        # 2. 处理聊天模型输出 (包含推理和回答)
        elif kind == "on_chat_model_stream":
            chunk = data.get("chunk", None)
            if not chunk:
                continue

            # 从事件元数据中获取触发该 LLM 调用的父节点名称
            # astream_events v2 在 metadata 中携带 langgraph_node
            metadata = event.get("metadata", {})
            source_node = metadata.get("langgraph_node", current_node)

            # --- A. 提取推理内容 (Thinking) ---
            reasoning = None
            if hasattr(chunk, "reasoning_content") and chunk.reasoning_content:
                reasoning = chunk.reasoning_content
            elif hasattr(chunk, "additional_kwargs") and "reasoning_content" in chunk.additional_kwargs:
                reasoning = chunk.additional_kwargs["reasoning_content"]

            if reasoning:
                yield "data: " + ResponseFactory.build_text(
                    reasoning, ContentKind.THINKING
                ).model_dump_json() + "\n\n"

            # --- B. 提取最终回答 (Answer) ---
            # 只有答案生成节点的输出才作为 ANSWER 透传，其余节点的 LLM 输出静默过滤
            content = chunk.content if hasattr(chunk, "content") else None
            if content and source_node in _ANSWER_NODES:
                yield "data: " + ResponseFactory.build_text(
                    content, ContentKind.ANSWER
                ).model_dump_json() + "\n\n"

        # 3. 处理工具调用 (PROCESS 类型)
        elif kind == "on_tool_start":
            tool_name = name
            yield "data: " + ResponseFactory.build_text(
                f"🔧 调用工具: {tool_name}", ContentKind.PROCESS
            ).model_dump_json() + "\n\n"

        # 4. 自定义事件 (支持从 Node 内部手动 yield 事件)
        elif kind == "on_custom_event":
             # 预留给未来扩展，例如检索到的文档详情
             pass

    # 5. 发送结束信号
    yield "data: " + ResponseFactory.build_finish().model_dump_json() + "\n\n"