"""
检索子图节点 (Retrieval SubGraph Nodes)

子图在受控范围内自主循环：dispatch → search → evaluate → (rewrite_query → search → evaluate) ...
核心亮点：确定性与智能性兼得 — 模型在受控范围内自主决策检索策略
"""
import json
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.tools.local.knowledge_base import query_knowledge
from infrastructure.tools.mcp.mcp_servers import get_search_mcp_client, get_baidu_mcp_client
from infrastructure.tools.local.service_station import (
    resolve_user_location_from_text_raw,
    query_nearest_repair_shops_by_coords_raw,
)
from infrastructure.utils.resilience import safe_parse_json, async_retry_with_timeout
from infrastructure.utils.observability import node_timer
from multi_agent.workflow.state import RetrievalSubState


@async_retry_with_timeout(timeout_s=20, max_retries=2)
async def _llm_evaluate(prompt: str) -> str:
    """LLM 评估调用（带超时重试）"""
    resp = await sub_model.ainvoke([{"role": "user", "content": prompt}])
    return resp.content if isinstance(resp.content, str) else str(resp.content)


@async_retry_with_timeout(timeout_s=20, max_retries=2)
async def _llm_rewrite(prompt: str) -> str:
    """LLM 改写调用（带超时重试）"""
    resp = await sub_model.ainvoke([{"role": "user", "content": prompt}])
    return resp.content.strip()


@node_timer("retrieval.dispatch")
def node_retrieval_dispatch(state: RetrievalSubState) -> dict:
    """
    分发节点：根据意图选择首选数据源，并将槽位信息融合到 query
    """
    intent = state.get("intent", "")
    query = state.get("query", "")
    slots = state.get("slots", {})

    source_map = {
        "tech_issue": "kb",
        "search_info": "web",
        "unknown": "web",
        "service_station": "local_tools",
        "poi_navigation": "local_tools",
    }
    source = source_map.get(intent, "web")

    # 将槽位关键信息融合到 query（避免检索时丢失上下文）
    slot_values = [v for k, v in slots.items() if v and k not in ("problem_description",)]
    if slot_values:
        enriched = f"{query} {''.join(slot_values)}"
        logger.info(f"[Retrieval Dispatch] query 融合槽位: '{query}' → '{enriched}'")
        query = enriched

    logger.info(f"[Retrieval Dispatch] intent={intent} → source={source}")
    return {"source": source, "query": query}


@node_timer("retrieval.search")
async def node_retrieval_search(state: RetrievalSubState) -> dict:
    """
    执行实际检索，根据 source 调用不同数据源
    """
    source = state.get("source", "web")
    query = state.get("query", "")
    intent = state.get("intent", "")
    slots = state.get("slots", {})

    logger.info(f"[Retrieval Search] source={source}, query={query[:50]}")

    docs = []
    if source == "kb":
        docs = await _search_kb(query)
    elif source == "web":
        docs = await _search_web(query)
    elif source == "local_tools":
        docs = await _search_local(intent, slots)

    logger.info(f"[Retrieval Search] 检索到 {len(docs)} 条结果")
    return {"documents": docs}


@node_timer("retrieval.evaluate")
async def node_retrieval_evaluate(state: RetrievalSubState) -> dict:
    """
    LLM 评估检索结果质量，决定是否需要重试
    """
    docs = state.get("documents", [])
    original_query = state.get("original_query", "")
    loop_count = state.get("loop_count", 0)
    source = state.get("source", "")

    # 无结果直接判定不足
    if not docs:
        suggestion = "switch_source" if source == "kb" else "pass"
        logger.info(f"[Evaluate] 无结果, suggestion={suggestion}")
        return {
            "is_sufficient": False,
            "suggestion": suggestion,
            "loop_count": loop_count + 1,
        }

    # 拼接检索结果摘要给 LLM 判断
    doc_summary = "\n".join(
        f"[{d.get('source','')}] {d.get('content','')[:200]}" for d in docs[:5]
    )

    prompt = f"""你是检索质量评估专家。请判断以下检索结果是否足够回答用户问题。

用户问题: {original_query}

检索结果:
{doc_summary}

评估标准：
- 只要检索结果与用户问题相关且包含有用信息，就判定为 sufficient=true
- 不要因为信息"不够完整"或"不够精确"就判 false，网络搜索结果本身就有局限性
- 只有检索结果完全无关或为空时才判 false

请用 JSON 格式回答（不要输出其他内容）:
{{"sufficient": true/false, "reason": "简短理由", "suggestion": "pass"或"retry_same"或"switch_source"}}"""

    try:
        text = await _llm_evaluate(prompt)
        result = safe_parse_json(text, {"sufficient": True, "suggestion": "pass"})
        is_sufficient = result.get("sufficient", True)
        suggestion = result.get("suggestion", "pass")
        logger.info(f"[Evaluate] sufficient={is_sufficient}, suggestion={suggestion}, reason={result.get('reason','')}")
    except Exception as e:
        logger.warning(f"[Evaluate] LLM 判断失败，默认通过: {e}")
        is_sufficient = True
        suggestion = "pass"

    return {
        "is_sufficient": is_sufficient,
        "suggestion": suggestion,
        "loop_count": loop_count + 1,
    }


@node_timer("retrieval.rewrite")
async def node_retrieval_rewrite(state: RetrievalSubState) -> dict:
    """
    LLM 改写查询词，融合 query expansion、关键词提取、换源策略
    替代原空转的 strategy_gen 节点
    """
    original_query = state.get("original_query", "")
    current_query = state.get("query", "")
    suggestion = state.get("suggestion", "retry_same")
    source = state.get("source", "")

    # 换源逻辑：只允许 kb → web 单向兜底
    if suggestion == "switch_source" and source == "kb":
        logger.info("[Rewrite] 切换数据源: kb → web (兜底)")
        return {"source": "web", "query": original_query}

    # 改写 query
    prompt = f"""你是搜索查询优化专家。当前查询未能获得满意结果，请改写查询词以提高检索效果。

原始问题: {original_query}
当前查询: {current_query}

要求：
1. 保留原始问题的核心语义，不要偏离主题
2. 去除口语化表达，使查询更精准
3. 不要堆砌大量同义词，改写结果应该是一个自然的搜索语句
4. 只返回改写后的查询词，不要解释

改写后的查询:"""

    try:
        new_query = await _llm_rewrite(prompt)
        if not new_query or len(new_query) > 200:
            new_query = original_query
        logger.info(f"[Rewrite] query 改写: '{current_query}' → '{new_query}'")
    except Exception as e:
        logger.warning(f"[Rewrite] LLM 改写失败，使用原始 query: {e}")
        new_query = original_query

    return {"query": new_query}


# ==================== 内部检索函数 ====================

async def _search_kb(query: str) -> list:
    try:
        answer = await query_knowledge(question=query)
        if not answer:
            return []
        return [{"source": "KnowledgeBase", "content": answer}]
    except Exception as e:
        logger.error(f"[Search KB] {e}")
        return []


async def _search_web(query: str) -> list:
    try:
        mcp_client = get_search_mcp_client()
        result = await mcp_client.call_tool("bailian_web_search", {"query": query})
        data = json.loads(result.content[0].text)
        results = data.get("pages", data.get("search_results", []))
        return [
            {"source": "WebSearch", "content": r.get("snippet", r.get("content", "")), "title": r.get("title", "")}
            for r in results[:3]
        ]
    except Exception as e:
        logger.error(f"[Search Web] {e}")
        return []


async def _search_local(intent: str, slots: dict) -> list:
    results = []
    if intent == "service_station":
        location = slots.get("location", "")
        try:
            loc_str = await resolve_user_location_from_text_raw(user_input=location)
            loc = json.loads(loc_str)
            if loc.get("ok") or loc.get("source") == "fallback":
                shop_str = query_nearest_repair_shops_by_coords_raw(lat=loc["lat"], lng=loc["lng"])
                shop = json.loads(shop_str)
                if shop.get("ok"):
                    for s in shop.get("data", []):
                        content = f"服务站: {s['service_station_name']}\n地址: {s['address']}\n电话: {s['phone']}\n距离: {s['distance_km']:.2f}km"
                        results.append({"source": "LocalDB", "content": content, "metadata": s})
        except Exception as e:
            logger.error(f"[Search Local] service_station error: {e}")

    elif intent == "poi_navigation":
        destination = slots.get("destination", "")
        try:
            client = get_baidu_mcp_client()
            res = await client.call_tool("map_poi_search", {"query": destination, "region": "全国"})
            data = json.loads(res.content[0].text)
            for poi in data.get("results", [])[:3]:
                results.append({"source": "BaiduMap", "content": f"地点: {poi['name']}\n地址: {poi.get('address', '不详')}", "metadata": poi})
        except Exception as e:
            logger.error(f"[Search Local] poi error: {e}")

    return results
