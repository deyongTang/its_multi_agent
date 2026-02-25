from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import main_model
from infrastructure.utils.observability import node_timer
from infrastructure.utils.resilience import async_retry_with_timeout
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import asyncio

def node_expand_query(state: AgentState) -> dict:
    """
    Fallback Trigger Node (Previously named Expand Query)
    
    Triggered when verification fails (e.g. KB returns empty/invalid).
    Increments retry_count to signal Strategy Node to switch source.
    """
    current_retry = state.get("retry_count", 0)
    new_retry = current_retry + 1
    
    # 明确日志：不是简单的查询扩展，而是源切换（兜底）
    logger.warning(f"[Fallback] Primary source failed/empty. Switching to fallback source (Retry {new_retry})...")
    
    return {
        "retry_count": new_retry,
        "error_log": state.get("error_log", []) + [f"Retry {new_retry}: Switched to fallback."]
    }

@node_timer("escalate")
def node_escalate(state: AgentState) -> dict:
    """
    Escalation Node
    
    Handover to human agent when all retries fail.
    """
    logger.error("Max retries reached. Escalating to human.")
    
    return {
        "need_human_help": True,
        "messages": [AIMessage(content="很抱歉，我尝试了多次仍无法找到准确信息。已为您转接人工客服，请稍候...")]
    }

@node_timer("generate_report")
async def node_generate_report(state: AgentState) -> dict:
    """
    Response Generation Node

    - 知识库场景：直接使用 RAG 答案（知识库已完成检索+生成）
    - 其他场景（web/local_tools/混合）：用 LLM 合成多源结果
    """
    docs = state.get("retrieved_documents", [])
    intent = state.get("current_intent", "general")

    logger.info(f"Generating report from {len(docs)} documents for intent: {intent}")

    if not docs:
        return {
            "messages": [AIMessage(content="抱歉，我没有找到相关的结果。您可以尝试换一种说法，或者联系人工客服。")]
        }

    # 判断是否全部来自知识库（已经是完整 RAG 答案）
    kb_docs = [d for d in docs if d.get("source") == "KnowledgeBase"]
    if kb_docs and len(kb_docs) == len(docs):
        answer = kb_docs[0].get("content", "")
        logger.info("[Report] 知识库场景，直接使用 RAG 答案")
        return {
            "final_report": {"summary": answer, "doc_count": len(docs)},
            "messages": [AIMessage(content=answer)]
        }

    # 多源场景：用 LLM 合成
    return await _synthesize_multi_source(state, docs, intent)


async def _synthesize_multi_source(state: AgentState, docs: list, intent: str) -> dict:
    """多源结果 LLM 合成（web/local_tools/混合场景）"""
    context_parts = []
    for i, doc in enumerate(docs):
        source = doc.get("source", "Unknown")
        content = doc.get("content", "")
        context_parts.append(f"--- 来源 {i+1} [{source}] ---\n{content}")

    context = "\n\n".join(context_parts)

    report_prompt = SystemMessage(content=f"""你是专业的 ITS 智能客服。根据参考资料回答用户问题。

意图类型: {intent}

参考资料：
{context}

要求：
- 只回答用户明确提问的内容，不要扩展到无关话题
- 从参考资料中提取与用户问题直接相关的信息，忽略无关内容
- 不编造事实；使用 Markdown 格式。""")

    # 追问场景：合并原始问题 + 补充信息，让 LLM 有完整上下文
    original_query = state.get("original_query") or ""
    last_user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            last_user_query = msg.content
            break
    if original_query and original_query != last_user_query:
        user_query = f"{original_query}（补充信息：{last_user_query}）"
    else:
        user_query = last_user_query or original_query

    async def _collect_stream():
        """收集 astream token，保持在节点上下文内以便 astream_events 追踪"""
        chunks = []
        async for chunk in main_model.astream([
            report_prompt,
            HumanMessage(content=f"用户的问题是：{user_query}")
        ]):
            if chunk.content:
                chunks.append(chunk.content)
        return "".join(chunks).strip()

    try:
        answer = await asyncio.wait_for(_collect_stream(), timeout=60)
        return {
            "final_report": {"summary": answer, "doc_count": len(docs)},
            "messages": [AIMessage(content=answer)]
        }
    except asyncio.TimeoutError:
        logger.error("Report generation timed out (60s)")
        return {"messages": [AIMessage(content="抱歉，生成回答超时，请稍后重试。")]}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        fallback = "根据找到的信息：\n\n" + "\n\n".join(
            [d.get("content", "")[:200] for d in docs[:2]]
        )
        return {"messages": [AIMessage(content=fallback)]}
