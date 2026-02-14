"""
意图识别节点 (node_intent) - 工业级分层架构

职责：
1. L1 识别：归口至 Technical, Location 或 Chitchat 专家。
2. L2 识别：细化具体的业务指令。
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from langchain_core.messages import HumanMessage, SystemMessage
import json

async def node_intent(state: AgentState) -> AgentState:
    try:
        messages = state.get("messages", [])
        if not messages:
            return {**state, "current_intent": "chitchat", "intent_confidence": 0.0}

        last_message = messages[-1]
        user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)

        intent_prompt = SystemMessage(content="""你是一个 ITS 多智能体系统的首席调度专家。
请根据用户输入，精准判定 L1（一级）和 L2（二级）意图。

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
        response = await sub_model.ainvoke([
            intent_prompt, 
            HumanMessage(content=user_query)
        ])

        result = json.loads(response.content.replace("```json", "").replace("```", "").strip())
        
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
