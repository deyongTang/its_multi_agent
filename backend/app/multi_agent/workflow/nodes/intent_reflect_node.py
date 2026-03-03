"""
意图反思节点 (node_intent_reflect)

触发时机：检索子图执行完毕，verify 判定结果为空（无法生成报告），
          且本轮还未发生过意图纠错（intent_retry_count == 0）。

职责：
  分析"用这个意图检索为什么会失败"，判断意图识别是否出错。
  - 意图确实错了 → 修正 current_intent，清空槽位，让 slot_filling 重新来过
  - 意图没错（只是没检索到）→ 不改，走 escalate
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.utils.resilience import safe_parse_json, async_retry_with_timeout
from infrastructure.utils.observability import node_timer


# 全量意图列表，让 LLM 从中选
CANDIDATE_INTENTS = [
    "tech_issue",       # 设备故障、软件问题、系统配置
    "search_info",      # 天气、新闻、股价等通用资讯
    "service_station",  # 查找官方维修站、售后服务中心
    "poi_navigation",   # 查找地点、POI 导航
    "chitchat",         # 闲聊
]


@async_retry_with_timeout(timeout_s=15, max_retries=1)
async def _llm_reflect(prompt: str) -> str:
    resp = await sub_model.ainvoke([{"role": "user", "content": prompt}])
    return resp.content if isinstance(resp.content, str) else str(resp.content)


@node_timer("intent_reflect")
async def node_intent_reflect(state: AgentState) -> dict:
    """
    意图反思节点：检索失败后反思意图是否识别正确。

    返回字段：
      - current_intent: 纠正后的意图（若意图不变则原值）
      - slots: 若意图变更则清空，避免旧槽位污染新流程
      - missing_slots: 清空，让 slot_filling 重新提取
      - intent_retry_count: +1，防止二次触发死循环
      - intent_corrected: True/False，供路由函数判断走向
    """
    original_query = state.get("original_query") or ""
    if not original_query:
        for msg in reversed(state.get("messages", [])):
            if msg.type == "human":
                original_query = msg.content
                break

    current_intent = state.get("current_intent", "")
    retry_count = state.get("intent_retry_count", 0)

    logger.info(f"[IntentReflect] 触发意图反思 | current_intent={current_intent} | query={original_query[:60]}")

    prompt = f"""你是意图识别纠错专家。

系统刚才将用户问题识别为意图 [{current_intent}]，并按此意图进行了检索，但未找到任何有用的结果。
这可能说明意图识别出错了。

用户原始问题：{original_query}

可选意图列表（含义）：
- tech_issue      : 设备故障、系统报错、软件问题、配置咨询（需要技术诊断）
- search_info     : 天气、新闻、股价、百科等通用资讯查询
- service_station : 寻找官方维修站、售后服务中心（有明确地点需求）
- poi_navigation  : 查找餐厅/景点/商场等 POI，或路线规划
- chitchat        : 闲聊、问候，无实际业务需求

请判断：原始问题的【正确意图】应该是什么？

只返回 JSON，不要解释：
{{"correct_intent": "从上方列表中选一个", "changed": true/false, "reason": "一句话说明"}}"""

    try:
        text = await _llm_reflect(prompt)
        result = safe_parse_json(text, {"correct_intent": current_intent, "changed": False})

        correct_intent = result.get("correct_intent", current_intent)
        changed = result.get("changed", False) and correct_intent != current_intent
        reason = result.get("reason", "")

        if changed:
            logger.info(
                f"[IntentReflect] 意图已纠正: {current_intent} → {correct_intent} | reason={reason}"
            )
            return {
                "current_intent": correct_intent,
                "slots": {},            # 清空旧槽位，避免污染新意图的 slot_filling
                "missing_slots": [],
                "retrieved_documents": [],
                "intent_retry_count": retry_count + 1,
                "intent_corrected": True,
            }
        else:
            logger.info(
                f"[IntentReflect] 意图无需纠正（{current_intent} 本身正确，检索失败另有原因）| reason={reason}"
            )
            return {
                "intent_retry_count": retry_count + 1,
                "intent_corrected": False,
            }

    except Exception as e:
        logger.warning(f"[IntentReflect] LLM 反思调用失败，跳过纠错: {e}")
        return {
            "intent_retry_count": retry_count + 1,
            "intent_corrected": False,
        }
