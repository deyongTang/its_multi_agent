"""
闲聊节点 (node_general_chat)

职责：
1. 处理非业务相关的对话（问候、寒暄）
2. 生成友好的回复
3. 引导用户提出业务问题
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.utils.observability import node_timer
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


@node_timer("general_chat")
async def node_general_chat(state: AgentState) -> AgentState:
    """
    闲聊节点

    Args:
        state: 当前状态

    Returns:
        更新后的状态（包含回复消息）
    """
    try:
        # 1. 获取用户消息
        messages = state.get("messages", [])
        if not messages:
            return {
                **state,
                "messages": [AIMessage(content="您好！有什么可以帮助您的吗？")],
            }

        last_message = messages[-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        logger.info(f"处理闲聊: {user_query[:50]}...")

        # 2. 构建闲聊 Prompt
        chat_prompt = SystemMessage(content="""你是联想智能客服助手。用户正在与你闲聊，请：

1. 友好、简短地回应用户
2. 适当引导用户提出业务问题
3. 不要过度发挥，保持专业

你可以帮助用户：
- 技术问题诊断（电脑故障、系统问题）
- 查找维修服务站
- 地点导航和路线规划
- 实时资讯查询

请直接返回回复文本，不要返回 JSON。
""")

        # 3. 调用 LLM 生成回复
        response = await sub_model.ainvoke([
            chat_prompt,
            HumanMessage(content=user_query)
        ])

        reply = response.content.strip()

        logger.info("闲聊回复生成完成")

        # 4. 更新状态
        return {
            **state,
            "messages": [AIMessage(content=reply)],
        }

    except Exception as e:
        logger.error(f"闲聊节点异常: {e}")
        state.setdefault("error_log", []).append(f"General chat error: {str(e)}")

        # 降级：使用通用回复
        return {
            **state,
            "messages": [AIMessage(content="您好！我是联想智能客服，有什么可以帮助您的吗？")],
        }
