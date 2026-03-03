from typing import Literal, List
from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger

def route_dispatch(state: AgentState) -> Literal["query_knowledge", "search_web", "query_local_tools"]:
    """
    分发路由器 (Primary Source Dispatcher)
    
    根据意图直接分发到首选数据源，不再经过复杂的策略计算。
    """
    intent = state.get("current_intent")
    
    logger.info(f"分发路由: 意图='{intent}'")

    # 1. 技术问题 -> 知识库 (KB First)
    if intent == "tech_issue":
        return "query_knowledge"
        
    # 2. 资讯/未知 -> 网络搜索
    elif intent == "search_info" or intent == "unknown":
        return "search_web"
        
    # 3. 位置服务 -> 本地工具
    elif intent in ["service_station", "poi_navigation"]:
        return "query_local_tools"
        
    # 兜底：默认去网络
    return "search_web"

def route_kb_check(state: AgentState) -> Literal["merge_results", "search_web"]:
    """
    KB 结果检查路由器 (Explicit Fallback Router)
    
    显式编排：KB 搜完后，直接在这里判断。
    - 有结果 -> 去汇总 (merge_results)
    - 没结果 -> 去网络搜索 (search_web)
    """
    docs = state.get("retrieved_documents", [])
    
    if docs:
        logger.info(f"KB 检索成功 ({len(docs)} 条)，进入汇总")
        return "merge_results"
    else:
        logger.warning("KB 检索无结果 (Miss)，显式触发网络搜索兜底 (Fallback -> Web)")
        return "search_web"

def route_verify_result(state: AgentState) -> Literal["generate_report", "intent_reflect", "escalate"]:
    """
    最终结果校验路由

    - 有文档          → generate_report
    - 无文档且首次失败 → intent_reflect（触发意图自纠错，最多 1 次）
    - 无文档且已纠错过 → escalate（兜底转人工）
    """
    docs = state.get("retrieved_documents", [])

    if docs:
        return "generate_report"

    # 首次检索失败：尝试意图反思
    if state.get("intent_retry_count", 0) < 1:
        logger.info("[RouteVerify] 检索结果为空，触发意图反思节点")
        return "intent_reflect"

    # 意图已纠错仍失败，或超过重试上限：转人工
    logger.warning("[RouteVerify] 意图纠错后仍无结果，升级人工处理")
    return "escalate"


def route_after_reflect(state: AgentState) -> Literal["slot_filling", "escalate"]:
    """
    意图反思后路由

    - 意图已修正 → slot_filling（用新意图重新提取槽位，走完整流程）
    - 意图未变   → escalate（反思确认意图本身没问题，只是确实找不到）
    """
    if state.get("intent_corrected", False):
        logger.info(f"[RouteReflect] 意图已纠正为 [{state.get('current_intent')}]，重新走 slot_filling")
        return "slot_filling"

    logger.info("[RouteReflect] 意图无需纠正，升级人工处理")
    return "escalate"
