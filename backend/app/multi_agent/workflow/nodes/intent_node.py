"""
意图识别节点 (node_intent)

职责：
1. 分析用户输入，识别意图类型
2. 计算意图置信度
3. 更新状态中的 current_intent 和 intent_confidence

意图类型：
- tech: 技术问题（故障诊断、操作指南）
- poi: POI 导航（地点查询、路线规划）
- service: 服务站查询（维修点查找）
- chitchat: 闲聊（非业务对话）
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from langchain_core.messages import HumanMessage, SystemMessage


async def node_intent(state: AgentState) -> AgentState:
    """
    意图识别节点

    Args:
        state: 当前状态

    Returns:
        更新后的状态（包含 current_intent 和 intent_confidence）
    """
    trace_id = state.get("trace_id", "-")

    try:
        # 1. 获取最新的用户消息
        messages = state.get("messages", [])
        if not messages:
            logger.warning(f"[{trace_id}] 意图识别失败：消息列表为空")
            return {
                **state,
                "current_intent": "chitchat",
                "intent_confidence": 0.0,
            }

        # 获取最后一条用户消息
        last_message = messages[-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        logger.info(f"[{trace_id}] 开始意图识别: {user_query[:50]}...")

        # 2. 构建意图识别 Prompt
        intent_prompt = SystemMessage(content="""你是一个意图分类专家。请分析用户输入，判断属于以下哪种意图：

1. **tech** - 技术问题
   - 电脑故障、蓝屏、无法开机
   - 软件安装、配置指南
   - 系统优化、性能问题
   - 实时资讯查询（天气、新闻）

2. **service** - 服务站查询
   - 查找维修点、服务站
   - 官方授权网点查询
   - 包含"维修"、"服务站"、"售后"等关键词

3. **poi** - POI 导航
   - 地点查询（商场、景点、餐厅）
   - 路线规划、导航
   - 周边设施查询

4. **chitchat** - 闲聊
   - 问候、寒暄
   - 非业务相关对话
   - 情感表达

请只返回 JSON 格式：
{
    "intent": "tech|service|poi|chitchat",
    "confidence": 0.0-1.0,
    "reason": "判断理由"
}""")

        # 3. 调用 LLM 进行意图识别
        response = await sub_model.ainvoke([
            intent_prompt,
            HumanMessage(content=user_query)
        ])

        # 4. 解析结果
        import json
        result_text = response.content

        # 尝试提取 JSON
        try:
            # 如果返回的是 markdown 格式，提取 JSON 部分
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            intent = result.get("intent", "chitchat")
            confidence = float(result.get("confidence", 0.5))
            reason = result.get("reason", "")

            logger.info(
                f"[{trace_id}] 意图识别完成: {intent} (置信度: {confidence:.2f})",
                extra={
                    "biz.intent": intent,
                    "biz.confidence": confidence,
                    "biz.reason": reason
                }
            )

        except Exception as e:
            logger.warning(f"[{trace_id}] 意图解析失败: {e}，使用默认值")
            intent = "chitchat"
            confidence = 0.5

        # 5. 更新状态
        return {
            **state,
            "current_intent": intent,
            "intent_confidence": confidence,
        }

    except Exception as e:
        logger.error(f"[{trace_id}] 意图识别节点异常: {e}")
        state.setdefault("error_log", []).append(f"Intent node error: {str(e)}")

        # 降级：默认为闲聊
        return {
            **state,
            "current_intent": "chitchat",
            "intent_confidence": 0.0,
        }
