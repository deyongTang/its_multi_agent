"""
意图路由函数 (route_intent)

根据识别的意图类型决定下一步流转：
- chitchat -> node_general_chat (闲聊节点)
- tech/service/poi -> node_slot_filling (槽位填充节点)
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger


def route_intent(state: AgentState) -> str:
    """
    意图路由函数

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    current_intent = state.get("current_intent", "chitchat")

    logger.info(f"意图路由: {current_intent}")

    # 闲聊直接进入闲聊节点
    if current_intent == "chitchat":
        return "general_chat"

    # 业务意图进入槽位填充
    # tech_issue, service_station, poi_navigation 需要槽位填充
    if current_intent in ["tech_issue", "service_station", "poi_navigation"]:
        return "slot_filling"

    # search_info 不需要槽位填充，直接进入槽位填充节点（会被快速放行）
    if current_intent == "search_info":
        return "slot_filling"

    # 默认：闲聊
    logger.warning(f"未知意图类型: {current_intent}，默认为闲聊")
    return "general_chat"
