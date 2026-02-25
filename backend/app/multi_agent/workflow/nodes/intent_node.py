"""
意图识别节点 (node_intent) - 工业级分层架构

职责：
1. L1 识别：归口至 Technical, Location 或 Chitchat 专家。
2. L2 识别：细化具体的业务指令。
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.utils.resilience import safe_parse_json
from infrastructure.utils.observability import node_timer
from langchain_core.messages import HumanMessage, SystemMessage


@node_timer("intent")
async def node_intent(state: AgentState) -> AgentState:
    try:
        messages = state.get("messages", [])
        if not messages:
            return {**state, "current_intent": "chitchat", "intent_confidence": 0.0}

        # 追问回复：current_intent 已从 session 恢复，直接复用，无需调用 LLM
        if state.get("ask_user_count", 0) > 0 and state.get("current_intent"):
            logger.info(f"追问回复，复用意图: {state['current_intent']}")
            return {**state}

        last_message = messages[-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        intent_prompt = SystemMessage(content="""你是一个 ITS 多智能体系统的首席调度专家。
请根据用户输入和对话历史，精准判定 L1（一级）和 L2（二级）意图。

【重要】如果历史对话中 AI 刚刚追问了某个信息（如地点、设备型号等），用户当前的回复是对该追问的补充，
则意图应与历史对话保持一致，不要重新识别为新意图。

### 意图体系：

1. **technical** (泛技术专家)
   - L2: **tech_issue** (故障诊断/运维)：报错、无法开机、软件安装、系统配置。
   - L2: **search_info** (通用资讯)：天气、股价、新闻、百科知识。

2. **location** (位置服务专家)
   - L2: **service_station** (服务站查询)：找官方维修点、售后中心。
   - L2: **poi_navigation** (POI 导航)：找餐厅、加油站、景点、路线规划。

3. **chitchat** (闲聊专家)
   - L2: **chitchat** (通用闲聊)：问候、寒暄、无关业务的对话。

请只返回 JSON：
{
    "l1_intent": "technical|location|chitchat",
    "l2_intent": "tech_issue|search_info|service_station|poi_navigation|chitchat",
    "confidence": 0.0-1.0,
    "reason": "判断依据"
}""")
        # 传入最近几轮对话历史，让 LLM 能识别追问场景
        history = messages[-6:-1]  # 最近 3 轮（不含当前消息）
        response = await sub_model.ainvoke([
            intent_prompt,
            *history,
            HumanMessage(content=user_query)
        ])

        text = response.content if isinstance(response.content, str) else str(response.content)
        result = safe_parse_json(text, {"l2_intent": "chitchat", "confidence": 0.0})
        
        # 将 L2 意图存入 current_intent 供业务节点使用
        intent = result.get("l2_intent", "chitchat")
        l1 = result.get("l1_intent", "chitchat")
        
        logger.info(f"意图识别 [L1:{l1} -> L2:{intent}]", extra={"biz.l1": l1, "biz.l2": intent})

        return {
            **state,
            "current_intent": intent, # 业务主要依赖 L2
            "intent_confidence": float(result.get("confidence", 0.0)),
            # 扩展状态以保存 L1，如果 state.py 中未定义，可放入 extra 字段或后续扩展
        }

    except Exception as e:
        logger.error(f"意图识别节点异常: {e}")
        return {**state, "current_intent": "chitchat", "intent_confidence": 0.0}
