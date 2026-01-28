"""
槽位填充节点 (node_slot_filling)

职责：
1. 根据意图类型提取必要的槽位信息
2. 检查哪些槽位缺失
3. 更新状态中的 slots 和 missing_slots

槽位定义：
- tech: [problem_description, device_model, os_version]
- service: [location, brand]
- poi: [destination, origin]
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from langchain_core.messages import HumanMessage, SystemMessage


# 定义各意图类型的必需槽位
REQUIRED_SLOTS = {
    "tech": ["problem_description"],  # 技术问题至少需要问题描述
    "service": ["location"],          # 服务站查询至少需要位置
    "poi": ["destination"],           # POI 导航至少需要目的地
    "chitchat": []                    # 闲聊不需要槽位
}


async def node_slot_filling(state: AgentState) -> AgentState:
    """
    槽位填充节点

    Args:
        state: 当前状态

    Returns:
        更新后的状态（包含 slots 和 missing_slots）
    """
    trace_id = state.get("trace_id", "-")
    current_intent = state.get("current_intent", "chitchat")

    try:
        logger.info(f"[{trace_id}] 开始槽位填充，意图: {current_intent}")

        # 1. 获取该意图类型需要的槽位
        required_slots = REQUIRED_SLOTS.get(current_intent, [])

        if not required_slots:
            logger.info(f"[{trace_id}] 意图 {current_intent} 不需要槽位填充")
            return {
                **state,
                "slots": state.get("slots", {}),
                "missing_slots": [],
            }

        # 2. 获取历史消息
        messages = state.get("messages", [])
        if not messages:
            return {
                **state,
                "slots": {},
                "missing_slots": required_slots,
            }

        # 3. 构建槽位提取 Prompt
        slot_prompt = SystemMessage(content=f"""你是一个信息提取专家。请从用户对话中提取以下槽位信息：

意图类型: {current_intent}
需要提取的槽位: {', '.join(required_slots)}

槽位说明：
- problem_description: 问题描述（技术问题的具体表现）
- device_model: 设备型号（如：ThinkPad X1, iPhone 14）
- os_version: 操作系统版本（如：Windows 10, macOS 13）
- location: 位置信息（如：北京海淀区、昌平区回龙观）
- brand: 品牌（如：联想、小米、苹果）
- destination: 目的地（如：天安门、中关村）
- origin: 出发地（如：回龙观、清华大学）

请只返回 JSON 格式：
{{
    "extracted_slots": {{
        "slot_name": "slot_value",
        ...
    }},
    "missing_slots": ["slot1", "slot2", ...]
}}

注意：
1. 只提取明确提到的信息，不要猜测
2. 如果信息不完整，在 missing_slots 中列出
3. 如果用户说"附近"、"最近"，location 可以标记为 "user_current_location"
""")

        # 4. 构建对话历史
        conversation = "\n".join([
            f"{'用户' if i % 2 == 0 else '助手'}: {msg.content if hasattr(msg, 'content') else str(msg)}"
            for i, msg in enumerate(messages[-5:])  # 只取最近5轮对话
        ])

        # 5. 调用 LLM 提取槽位
        response = await sub_model.ainvoke([
            slot_prompt,
            HumanMessage(content=f"对话历史：\n{conversation}")
        ])

        # 6. 解析结果
        import json
        result_text = response.content

        try:
            # 提取 JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            extracted_slots = result.get("extracted_slots", {})
            missing_slots = result.get("missing_slots", [])

            # 7. 合并已有槽位（保留历史槽位）
            current_slots = state.get("slots", {})
            updated_slots = {**current_slots, **extracted_slots}

            logger.info(
                f"[{trace_id}] 槽位填充完成: 已提取 {len(extracted_slots)} 个，缺失 {len(missing_slots)} 个",
                extra={
                    "biz.extracted_slots": list(extracted_slots.keys()),
                    "biz.missing_slots": missing_slots
                }
            )

            return {
                **state,
                "slots": updated_slots,
                "missing_slots": missing_slots,
            }

        except Exception as e:
            logger.warning(f"[{trace_id}] 槽位解析失败: {e}")
            return {
                **state,
                "slots": state.get("slots", {}),
                "missing_slots": required_slots,
            }

    except Exception as e:
        logger.error(f"[{trace_id}] 槽位填充节点异常: {e}")
        state.setdefault("error_log", []).append(f"Slot filling error: {str(e)}")

        return {
            **state,
            "slots": state.get("slots", {}),
            "missing_slots": REQUIRED_SLOTS.get(current_intent, []),
        }
