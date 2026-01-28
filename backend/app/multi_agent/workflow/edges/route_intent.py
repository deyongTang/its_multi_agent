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
    trace_id = state.get("trace_id", "-")
    current_intent = state.get("current_intent", "chitchat")

    logger.info(f"[{trace_id}] 意图路由: {current_intent}")

    # 闲聊直接进入闲聊节点
    if current_intent == "chitchat":
        return "general_chat"

    # 业务意图进入槽位填充
    if current_intent in ["tech", "service", "poi"]:
        return "slot_filling"

    # 默认：闲聊
    logger.warning(f"[{trace_id}] 未知意图类型: {current_intent}，默认为闲聊")
    return "general_chat"
