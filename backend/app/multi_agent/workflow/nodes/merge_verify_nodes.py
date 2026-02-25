"""
结果校验节点 (Verify Node)

使用 LLM 做最终质量把关：
- 检索结果和用户问题是否匹配
- 是否存在矛盾信息
- 是否需要人工介入
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.utils.resilience import safe_parse_json, async_retry_with_timeout
from infrastructure.utils.observability import node_timer


@async_retry_with_timeout(timeout_s=20, max_retries=2)
async def _llm_verify(prompt: str) -> str:
    """LLM 质量校验调用（带超时重试）"""
    resp = await sub_model.ainvoke([{"role": "user", "content": prompt}])
    return resp.content if isinstance(resp.content, str) else str(resp.content)


@node_timer("verify")
async def node_verify(state: AgentState) -> dict:
    """
    LLM 质量校验节点，替代原空壳实现。
    由后续 route_verify_result 根据 retrieved_documents 是否为空决定走 report 还是 escalate。
    """
    docs = state.get("retrieved_documents", [])

    if not docs:
        logger.info("[Verify] 无检索结果，跳过质量校验")
        return {}

    # 优先用原始问题（追问场景），否则取最后一条 user 消息
    user_query = state.get("original_query") or ""
    if not user_query:
        for msg in reversed(state.get("messages", [])):
            if msg.type == "human":
                user_query = msg.content
                break

    # LLM 质量判断
    doc_summary = "\n".join(
        f"[{d.get('source', '')}] {d.get('content', '')[:150]}" for d in docs[:5]
    )

    prompt = f"""判断以下检索结果能否回答用户问题。只返回 JSON。

规则：只要检索结果与问题相关且包含有用信息就判 pass=true，不要因信息不完整就判 false。

用户问题: {user_query}

检索结果:
{doc_summary}

{{"pass": true/false, "reason": "简短理由"}}"""

    try:
        text = await _llm_verify(prompt)
        result = safe_parse_json(text, {"pass": True})

        if not result.get("pass", True):
            logger.warning(f"[Verify] 质量校验未通过: {result.get('reason', '')}")
            return {"retrieved_documents": []}

        logger.info(f"[Verify] 质量校验通过: {result.get('reason', '')}")
    except Exception as e:
        logger.warning(f"[Verify] LLM 校验异常，默认通过: {e}")

    return {}
