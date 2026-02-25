"""
槽位填充节点 (node_slot_filling) - 工业级重构

职责：
1. 根据 L2 意图，提取并验证业务必需的槽位 (Slots)。
2. search_info 意图走 LLM 动态槽位判断（搜索类查询所需信息不固定）。
"""

import json
from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.utils.resilience import safe_parse_json
from infrastructure.utils.observability import node_timer
from langchain_core.messages import HumanMessage, SystemMessage

# 定义 L2 意图的必需槽位
REQUIRED_SLOTS = {
    "tech_issue": ["problem_description", "device_model"], # 故障诊断必须知道什么东西坏了
    "service_station": ["location"],                       # 维修点必须知道用户在哪
    "poi_navigation": ["destination"],                     # 导航必须知道去哪
    # search_info 槽位由 LLM 动态判断，不在此硬编码
    "search_info": None,
    "chitchat": []
}


async def _dynamic_slot_filling(state: AgentState, intent: str) -> AgentState:
    """search_info 等动态意图：让 LLM 判断用户查询是否缺少关键信息"""
    messages = state.get("messages", [])
    conversation = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-3:]])

    try:
        prompt = SystemMessage(content="""你是搜索意图分析专家。判断用户查询是否缺少执行搜索所需的关键信息。

规则：
- 天气/气温/降雨等气象查询：必须有【具体地点】，否则缺失
- 股价/行情查询：必须有【股票名称或代码】，否则缺失
- 新闻/资讯/科技动态：无需额外信息，直接搜索
- 其他查询：判断是否有足够信息执行搜索
- 【重要】如果当前问题缺少信息，但对话历史中已有该信息，则从历史中提取，不算缺失

示例：
- "今天北京天气" → {"extracted_slots": {"地点": "北京"}, "missing_slots": [], "is_sufficient": true}
- "明天天气怎么样" → {"extracted_slots": {}, "missing_slots": ["地点"], "is_sufficient": false}
- 历史有"深圳"，当前问"后天呢" → {"extracted_slots": {"地点": "深圳"}, "missing_slots": [], "is_sufficient": true}

只返回 JSON，不要解释：{"extracted_slots": {...}, "missing_slots": [...], "is_sufficient": true/false}""")

        response = await sub_model.ainvoke([
            prompt,
            HumanMessage(content=f"最近对话：\n{conversation}")
        ])

        text = response.content if isinstance(response.content, str) else str(response.content)
        result = safe_parse_json(text, {"extracted_slots": {}, "missing_slots": [], "is_sufficient": True})

        slots = {**state.get("slots", {}), **result.get("extracted_slots", {})}
        missing = result.get("missing_slots", []) if not result.get("is_sufficient") else []

        logger.info(f"[search_info] 动态槽位判断: slots={slots}, missing={missing}")
        # 槽位满足时重置追问计数，避免下一轮新问题被误判为追问回复
        ask_count = 0 if not missing else state.get("ask_user_count", 0)
        return {**state, "slots": slots, "missing_slots": missing, "ask_user_count": ask_count}

    except Exception as e:
        logger.error(f"动态槽位判断异常: {e}")
        # 异常时放行，不阻塞流程
        return {**state, "slots": state.get("slots", {}), "missing_slots": []}


@node_timer("slot_filling")
async def node_slot_filling(state: AgentState) -> AgentState:
    current_intent = state.get("current_intent") or "chitchat"
    
    # 1. 快速放行 / 动态槽位判断
    required_slots = REQUIRED_SLOTS.get(current_intent, [])
    if required_slots is None:
        # search_info 等动态意图：让 LLM 判断是否需要补充信息
        return await _dynamic_slot_filling(state, current_intent)
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

        text = response.content if isinstance(response.content, str) else str(response.content)
        result = safe_parse_json(text, {"extracted_slots": {}, "missing_slots": required_slots})
        
        # 3. 合并新老槽位
        old_slots = state.get("slots", {})
        new_slots = result.get("extracted_slots", {})
        merged_slots = {**old_slots, **new_slots}
        
        raw_missing = result.get("missing_slots", [])
        # 过滤：只保留当前意图真正需要的槽位，防止 LLM 返回其他意图的槽位
        missing = [s for s in raw_missing if s in required_slots]

        logger.info(f"槽位提取结果: {merged_slots}, LLM缺失: {raw_missing}, 过滤后缺失: {missing}")

        ask_count = 0 if not missing else state.get("ask_user_count", 0)
        return {
            **state,
            "slots": merged_slots,
            "missing_slots": missing,
            "ask_user_count": ask_count,
        }

    except Exception as e:
        logger.error(f"槽位填充节点异常: {e}")
        return {**state, "missing_slots": required_slots} # 异常时保守处理，标记缺失