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

def route_verify_result(state: AgentState) -> Literal["generate_report", "escalate"]:
    """
    最终结果校验
    """
    docs = state.get("retrieved_documents", [])
    
    if docs:
        return "generate_report"
    
    # 如果 Web 搜完还是空的，或者 KB->Web 还是空的，直接转人工
    # 不再进行循环重试
    return "escalate"
