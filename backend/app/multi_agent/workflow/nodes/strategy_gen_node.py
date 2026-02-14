"""
策略生成节点 (node_strategy_gen) - Active Retrieval Protocol

职责：
1. 根据 L2 意图，生成检索参数 (Query Expansion/Rewriting)。
2. 【V3变更】不再负责源切换逻辑，源切换由 Graph 拓扑显式控制。
"""

from multi_agent.workflow.state import AgentState, RetrievalStrategy
from infrastructure.logging.logger import logger

def node_strategy_gen(state: AgentState) -> dict:
    intent = state.get("current_intent")
    slots = state.get("slots", {})
    retry_count = state.get("retry_count", 0)
    
    logger.info(f"正在制定检索策略 (V3 - Explicit): 意图={intent}")
    
    strategy: RetrievalStrategy = {
        "intent_type": intent or "unknown",
        "query_tags": [],
        "search_kwargs": {}
    }
    
    # 填充业务参数（如时间范围、限制条数等）
    if intent == "tech_issue":
        # 提取关键设备信息作为 tag
        if "device_model" in slots:
            strategy["query_tags"].append(slots["device_model"])
            
    # 如果是重试，标记需要扩展查询 (Query Expansion)
    # 具体怎么扩展由各 Search Node 内部处理（例如调用 LLM 改写 Query）
    if retry_count > 0:
        strategy["search_kwargs"]["expand_query"] = True

    return {"retrieval_strategy": strategy}