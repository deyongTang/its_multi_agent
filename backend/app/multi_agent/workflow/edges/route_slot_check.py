"""
槽位检查路由函数 (route_slot_check)

根据槽位填充情况决定下一步流转：
- 有缺失槽位 -> node_ask_user (追问节点)
- 槽位完整 -> END (Phase 1 暂时结束，Phase 2 会改为 node_strategy_gen)
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger


def route_slot_check(state: AgentState) -> str:
    """
    槽位检查路由函数

    Args:
        state: 当前状态

    Returns:
        下一个节点名称
    """
    missing_slots = state.get("missing_slots", [])

    logger.info(f"槽位检查: 缺失 {len(missing_slots)} 个槽位")

    # 有缺失槽位，需要追问
    if missing_slots:
        logger.info(f"槽位不完整，进入追问流程: {missing_slots}")
        return "ask_user"

    # 槽位完整，进入检索子图
    logger.info("槽位完整，进入检索子图")
    return "retrieval"
