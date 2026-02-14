"""
追问节点 (node_ask_user)

职责：
1. 根据缺失的槽位生成追问话术
2. 将追问消息添加到 messages 中
3. 触发中断，等待用户回复

注意：此节点执行后会触发 interrupt，工作流暂停
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


async def node_ask_user(state: AgentState) -> AgentState:
    """
    追问节点

    Args:
        state: 当前状态

    Returns:
        更新后的状态（包含追问消息）
    """
    missing_slots = state.get("missing_slots", [])
    current_intent = state.get("current_intent", "chitchat")
    ask_user_count = state.get("ask_user_count", 0)

    try:
        logger.info(f"生成追问话术，缺失槽位: {missing_slots}")

        # 1. 防止无限追问（最多追问 3 次）
        if ask_user_count >= 3:
            logger.warning("追问次数超限，转人工处理")
            return {
                **state,
                "need_human_help": True,
                "messages": [AIMessage(content="抱歉，我需要更多信息才能帮助您。请联系人工客服获取进一步支持。")],
            }

        # 2. 构建追问 Prompt
        ask_prompt = SystemMessage(content=f"""你是一个友好的客服助手。用户的请求缺少一些必要信息，请生成一个自然、友好的追问。

意图类型: {current_intent}
缺失的槽位: {', '.join(missing_slots)}

槽位说明：
- problem_description: 问题的具体表现
- device_model: 设备型号
- os_version: 操作系统版本
- location: 位置信息
- brand: 品牌
- destination: 目的地
- origin: 出发地

要求：
1. 语气自然、友好
2. 一次只问 1-2 个最重要的信息
3. 给出示例帮助用户理解
4. 不要使用技术术语

请直接返回追问文本，不要返回 JSON。
""")

        # 3. 调用 LLM 生成追问
        response = await sub_model.ainvoke([
            ask_prompt,
            HumanMessage(content=f"请为缺失的槽位生成追问：{', '.join(missing_slots)}")
        ])

        question = response.content.strip()

        logger.info(
            f"追问生成完成: {question[:50]}...",
            extra={
                "biz.ask_count": ask_user_count + 1,
                "biz.missing_slots": missing_slots
            }
        )

        # 4. 更新状态
        return {
            **state,
            "messages": [AIMessage(content=question)],
            "ask_user_count": ask_user_count + 1,
        }

    except Exception as e:
        logger.error(f"追问节点异常: {e}")
        state.setdefault("error_log", []).append(f"Ask user error: {str(e)}")

        # 降级：使用通用追问
        generic_question = "请提供更多详细信息，以便我更好地帮助您。"
        return {
            **state,
            "messages": [AIMessage(content=generic_question)],
            "ask_user_count": ask_user_count + 1,
        }
