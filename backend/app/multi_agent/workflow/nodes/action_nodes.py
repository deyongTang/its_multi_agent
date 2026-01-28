from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger

def node_expand_query(state: AgentState) -> dict:
    """
    Query Expansion Node (Retry Loop)
    
    Triggered when verification fails.
    1. Increments retry_count.
    2. Relaxes search constraints (e.g. removes filters).
    """
    current_retry = state.get("retry_count", 0)
    new_retry = current_retry + 1
    
    logger.warning(f"Search failed. Expanding query (Retry {new_retry})...")
    
    # Logic to relax strategy is actually applied in 'node_strategy_gen' 
    # based on the retry_count or we update strategy here directly.
    # Here we simulate updating the 'error_log' to trigger a different strategy next time.
    
    return {
        "retry_count": new_retry,
        "error_log": [f"Retry {new_retry}: Zero results found."]
    }

def node_escalate(state: AgentState) -> dict:
    """
    Escalation Node
    
    Handover to human agent when all retries fail.
    """
    from langchain_core.messages import AIMessage
    
    logger.error("Max retries reached. Escalating to human.")
    
    return {
        "need_human_help": True,
        "messages": [AIMessage(content="很抱歉，我尝试了多次仍无法找到准确信息。已为您转接人工客服，请稍候...")]
    }

def node_generate_report(state: AgentState) -> dict:
    """
    Response Generation Node
    
    Synthesizes the final answer from retrieved documents.
    """
    from langchain_core.messages import AIMessage
    
    docs = state.get("retrieved_documents", [])
    
    # TODO: Call LLM to summarize docs
    summary = "根据检索结果：\n" + "\n".join([d.get("content", "") for d in docs[:3]])
    
    return {
        "final_report": {"summary": summary},
        "messages": [AIMessage(content=summary)]
    }
