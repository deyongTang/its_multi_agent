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

    - 有文档                                       → generate_report
    - 无文档 & 本地工具意图 & 首次失败              → intent_reflect
    - 无文档 & 其他意图（tech/search）              → escalate
    - 无文档 & 已纠错过                            → escalate

    意图纠错是最后手段，仅在"走本地工具路径（service_station/poi_navigation）
    且确实找不到数据"时触发。tech_issue 和 search_info 的检索子图内部
    已通过 rewrite 换源到网络搜索兜底，无需再纠错意图。
    """
    docs = state.get("retrieved_documents", [])

    if docs:
        return "generate_report"

    intent = state.get("current_intent", "")
    LOCAL_TOOLS_INTENTS = {"service_station", "poi_navigation"}

    # 只有本地工具意图（无网络兜底）且首次失败，才值得反思意图
    if intent in LOCAL_TOOLS_INTENTS and state.get("intent_retry_count", 0) < 1:
        logger.info(f"[RouteVerify] 检索为空 | 意图={intent}（本地工具路径，无网络兜底），触发意图反思")
        return "intent_reflect"

    # tech_issue / search_info：子图内部已有 KB→Web 换源兜底，无需纠错意图
    # 或已纠错过一次仍无结果：直接转人工
    logger.warning(f"[RouteVerify] 检索为空 | 意图={intent}，升级人工处理")
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
