"""
槽位填充节点 (node_slot_filling) - 工业级重构

职责：
1. 根据 L2 意图，提取并验证业务必需的槽位 (Slots)。
2. 【关键】识别非槽位依赖意图（如 search_info），直接放行。
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from langchain_core.messages import HumanMessage, SystemMessage
import json

# 定义 L2 意图的必需槽位
REQUIRED_SLOTS = {
    "tech_issue": ["problem_description", "device_model"], # 故障诊断必须知道什么东西坏了
    "service_station": ["location"],                       # 维修点必须知道用户在哪
    "poi_navigation": ["destination"],                     # 导航必须知道去哪
    # 以下意图不需要槽位填充，直接跳过
    "search_info": [], 
    "chitchat": []
}

async def node_slot_filling(state: AgentState) -> AgentState:
    current_intent = state.get("current_intent", "chitchat")
    
    # 1. 快速放行逻辑：如果意图不在必需槽位清单中，或者清单为空，直接返回
    required_slots = REQUIRED_SLOTS.get(current_intent, [])
    if not required_slots:
        logger.info(f"意图 [{current_intent}] 无需槽位填充，直接放行")
        return {**state, "slots": state.get("slots", {}), "missing_slots": []}

    try:
        logger.info(f"执行槽位提取，目标意图: {current_intent}")
        messages = state.get("messages", [])
        
        # 获取当前已有的槽位信息
        current_slots = state.get("slots", {})
        current_slots_str = json.dumps(current_slots, ensure_ascii=False)

        # 2. 构建提取 Prompt
        # 核心优化：将【已知槽位】注入 Prompt，让 LLM 负责 "追加 vs 覆盖" 的语义判断
        slot_prompt = SystemMessage(content=f"""你是一个高精度的业务数据提取专家。
请根据用户对话和【已知槽位】，提取或更新意图 [{current_intent}] 所需的槽位。

【已知槽位】:
{current_slots_str}

必需槽位定义：
- problem_description: 故障或咨询的具体现象（如：蓝屏、无法充电）。如果是补充信息，请合并旧值。
- device_model: 设备型号或系列（如：ThinkPad X1, 联想笔记本, Win10系统）。通常为覆盖更新。
- location: 用户所在位置或目标区域
- destination: 导航目的地

【提取规则】：
1. 增量更新：仅返回需要【修改】或【新增】的槽位。
2. 智能合并：
   - 纠正（"不是A是B"） -> 覆盖旧值
   - 补充（"还有C"） -> 在旧值基础上追加（如 "A, C"）
3. 保持：如果槽位信息未变，不要包含在返回结果中。

请严格只返回 JSON：
{{
    "extracted_slots": {{ "slot_name": "value" }},
    "missing_slots": ["缺失的必需槽位名称"]
}}""")

        conversation = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-3:]])
        
        response = await sub_model.ainvoke([
            slot_prompt,
            HumanMessage(content=f"最近对话：\n{conversation}")
        ])

        result = json.loads(response.content.replace("```json", "").replace("```", "").strip())
        
        # 3. 合并新老槽位
        old_slots = state.get("slots", {})
        new_slots = result.get("extracted_slots", {})
        merged_slots = {**old_slots, **new_slots}
        
        missing = result.get("missing_slots", [])
        
        logger.info(f"槽位提取结果: {merged_slots}, 缺失: {missing}")

        return {
            **state,
            "slots": merged_slots,
            "missing_slots": missing
        }

    except Exception as e:
        logger.error(f"槽位填充节点异常: {e}")
        return {**state, "missing_slots": required_slots} # 异常时保守处理，标记缺失