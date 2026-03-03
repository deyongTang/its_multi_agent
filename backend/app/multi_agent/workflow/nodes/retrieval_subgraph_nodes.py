"""
检索子图节点 (Retrieval SubGraph Nodes)

子图在受控范围内自主循环：dispatch → search → evaluate → (rewrite_query → search → evaluate) ...
核心亮点：确定性与智能性兼得 — 模型在受控范围内自主决策检索策略
"""
import json
from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.tools.local.knowledge_base import query_knowledge
from infrastructure.tools.mcp.mcp_servers import create_search_mcp_client, create_baidu_mcp_client
from infrastructure.tools.local.service_station import (
    resolve_user_location_from_text_raw,
    query_nearest_repair_shops_by_coords_raw,
)
from infrastructure.utils.resilience import async_retry_with_timeout
from infrastructure.utils.observability import node_timer
from multi_agent.workflow.state import RetrievalSubState
from multi_agent.workflow.nodes.evaluation_strategies import get_strategy


@async_retry_with_timeout(timeout_s=20, max_retries=2)
async def _llm_rewrite(prompt: str) -> str:  # noqa: keep for rewrite node
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
    评估检索结果质量，根据数据源选择对应的评估策略。

    策略路由:
      kb          → KBEvaluationStrategy       (规则判断，KB 内部已 Rerank 保障质量)
      web         → WebEvaluationStrategy       (LLM 语义评估)
      local_tools → LocalToolsEvaluationStrategy(结构字段校验)

    新增数据源时只需在 evaluation_strategies.STRATEGY_REGISTRY 注册，此节点无需修改。
    """
    source = state.get("source", "")
    docs = state.get("documents", [])
    original_query = state.get("original_query", "")
    loop_count = state.get("loop_count", 0)

    strategy = get_strategy(source)
    result = await strategy.evaluate(docs=docs, original_query=original_query)

    logger.info(
        f"[Evaluate] source={source} | sufficient={result.is_sufficient} "
        f"| suggestion={result.suggestion} | reason={result.reason}"
    )

    return {
        "is_sufficient": result.is_sufficient,
        "suggestion": result.suggestion,
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
        async with create_search_mcp_client() as mcp_client:
            result = await mcp_client.call_tool("bailian_web_search", {"query": query})
            data = json.loads(result.content[0].text)
            results = data.get("pages", data.get("search_results", []))
            return [
                {"source": "WebSearch", "content": r.get("snippet", r.get("content", "")), "title": r.get("title", "")}
                for r in results[:3]
            ]
    except Exception as e:
        logger.error(f"[Search Web] {type(e).__name__}: {e}", exc_info=True)
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
            async with create_baidu_mcp_client() as client:
                res = await client.call_tool("map_poi_search", {"query": destination, "region": "全国"})
                data = json.loads(res.content[0].text)
                for poi in data.get("results", [])[:3]:
                    results.append({"source": "BaiduMap", "content": f"地点: {poi['name']}\n地址: {poi.get('address', '不详')}", "metadata": poi})
        except Exception as e:
            logger.error(f"[Search Local] poi error: {e}")

    return results
