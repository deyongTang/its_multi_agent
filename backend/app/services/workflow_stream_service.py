from collections.abc import AsyncGenerator
from typing import Any
from utils.response_util import ResponseFactory
from schemas.response import ContentKind
from infrastructure.logging.logger import logger

async def process_workflow_stream(workflow_stream: AsyncGenerator) -> AsyncGenerator:
    """
    处理 LangGraph 异步事件流并转换为前端 SSE 格式
    
    Args:
        workflow_stream: LangGraph astream_events 生成器
    """
    
    async for event in workflow_stream:
        kind = event.get("event")
        name = event.get("name")
        data = event.get("data")
        
        # 1. 处理节点开始/结束事件 (PROCESS 类型)
        if kind == "on_chain_start" and name == "LangGraph":
             pass # 流程开始
             
        elif kind == "on_node_start":
            node_name = name
            # 过滤掉内部节点名称，只展示有意义的节点
            if node_name not in ["__start__", "__end__", "LangGraph"]:
                text = f"进入环节: {node_name}"
                yield "data: " + ResponseFactory.build_text(
                    f"🔄 {text}", ContentKind.PROCESS
                ).model_dump_json() + "\n\n"

        # 2. 处理聊天模型输出 (包含推理和回答)
        elif kind == "on_chat_model_stream":
            chunk = data.get("chunk", None)
            if not chunk:
                continue
                
            # --- A. 提取推理内容 (Thinking) ---
            # 适配 OpenAI 兼容接口的 reasoning_content
            # DeepSeek R1 等模型通常把推理放在这里
            reasoning = None
            
            # 尝试从标准 delta 中获取 (v1)
            if hasattr(chunk, "reasoning_content") and chunk.reasoning_content:
                reasoning = chunk.reasoning_content
            # 尝试从 additional_kwargs 中获取 (v2/OneAPI)
            elif hasattr(chunk, "additional_kwargs") and "reasoning_content" in chunk.additional_kwargs:
                reasoning = chunk.additional_kwargs["reasoning_content"]
            # 尝试从 message_content 的 token 级属性获取 (LangChain Specific)
            elif hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content.startswith("<thinking>"):
                # 如果模型直接吐出 XML 标签，需要自己解析（暂不实现复杂解析，假设 API 已经结构化）
                pass
            
            if reasoning:
                yield "data: " + ResponseFactory.build_text(
                    reasoning, ContentKind.THINKING
                ).model_dump_json() + "\n\n"

            # --- B. 提取最终回答 (Answer) ---
            content = chunk.content if hasattr(chunk, "content") else None
            if content:
                yield "data: " + ResponseFactory.build_text(
                    content, ContentKind.ANSWER
                ).model_dump_json() + "\n\n"

        # 3. 处理工具调用 (PROCESS 类型)
        elif kind == "on_tool_start":
            tool_name = name
            tool_input = data.get("input", "")
            text = f"调用工具: {tool_name}"
            yield "data: " + ResponseFactory.build_text(
                f"🔧 {text}", ContentKind.PROCESS
            ).model_dump_json() + "\n\n"
            
        # 4. 自定义事件 (支持从 Node 内部手动 yield 事件)
        elif kind == "on_custom_event":
             # 预留给未来扩展，例如检索到的文档详情
             pass

    # 5. 发送结束信号
    yield "data: " + ResponseFactory.build_finish().model_dump_json() + "\n\n"