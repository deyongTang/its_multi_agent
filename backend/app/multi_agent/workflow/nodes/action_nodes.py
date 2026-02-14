from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import main_model
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

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

async def node_generate_report(state: AgentState) -> dict:
    """
    Response Generation Node
    
    Synthesizes the final answer from retrieved documents using the reasoning model.
    """
    docs = state.get("retrieved_documents", [])
    intent = state.get("current_intent", "general")
    
    logger.info(f"Generating report from {len(docs)} documents for intent: {intent}")
    
    if not docs:
        return {
            "messages": [AIMessage(content="抱歉，我没有找到相关的结果。您可以尝试换一种说法，或者联系人工客服。")]
        }

    # 1. 准备背景资料
    context_parts = []
    for i, doc in enumerate(docs):
        source = doc.get("source", "Unknown")
        content = doc.get("content", "")
        context_parts.append(f"--- 来源 {i+1} [{source}] ---\n{content}")
    
    context = "\n\n".join(context_parts)
    
    # 2. 构建合成 Prompt
    report_prompt = SystemMessage(content=f"""你是一个专业的 ITS 智能客服。请根据提供的多源参考资料，为用户生成一个准确、完整、专业的回答。

意图类型: {intent}

参考资料：
{context}

写作指南：
1. 优先度：如果资料冲突，以知识库(KnowledgeBase)或本地数据库(LocalDB)为准。
2. 结构化：使用分步说明、列表或表格（如果适用）。
3. 准确性：不要编造事实。如果资料中没有答案，请诚实说明。
4. 品牌一致性：作为联想智能客服，保持专业、礼貌、高效。
5. 去冗余：合并多个来源中的重复信息。

直接返回回复文本，不要返回 JSON 格式。可以使用 Markdown 格式。
""")

    # 获取最后一条用户消息作为上下文
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    try:
        response = await main_model.ainvoke([
            report_prompt,
            HumanMessage(content=f"用户的问题是：{user_query}")
        ])
        
        answer = response.content.strip()
        
        return {
            "final_report": {"summary": answer, "doc_count": len(docs)},
            "messages": [AIMessage(content=answer)]
        }
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        # 降级：简单拼接
        fallback_answer = "根据找到的信息：\n\n" + "\n\n".join([d.get("content", "")[:200] for d in docs[:2]])
        return {
            "messages": [AIMessage(content=fallback_answer)]
        }
