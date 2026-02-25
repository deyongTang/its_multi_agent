"""
追问结果路由函数 (route_ask_user_result)

- 追问超限（need_human_help=True） -> escalate
- 正常追问 -> end（等待用户下一轮输入）
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger


def route_ask_user_result(state: AgentState) -> str:
    if state.get("need_human_help"):
        logger.info("追问超限，转人工客服")
        return "escalate"
    return "end"
