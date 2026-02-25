import asyncio
import json
from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger 
from infrastructure.tools.local.knowledge_base import query_knowledge
from infrastructure.tools.mcp.mcp_servers import get_search_mcp_client, get_baidu_mcp_client
from infrastructure.tools.local.service_station import resolve_user_location_from_text_raw, query_nearest_repair_shops_by_coords_raw

def get_last_user_query(state: AgentState) -> str:
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if msg.type == "human":
            return msg.content
    return ""

async def node_query_knowledge(state: AgentState) -> dict:
    """
    知识库节点：调用知识库 /query_sync 接口，获取完整 RAG 答案。
    知识库内部已完成检索+LLM生成，这里直接拿最终答案。
    """
    user_query = get_last_user_query(state)
    logger.info(f"[Knowledge Service] Querying: {user_query}")

    try:
        answer = await query_knowledge(question=user_query)

        if not answer:
            logger.info("[Knowledge Service] 知识库未返回答案")
            return {"retrieved_documents": []}

        docs = [{"source": "KnowledgeBase", "content": answer}]
        logger.info(f"[Knowledge Service] 获取到 RAG 答案，长度: {len(answer)}")
        return {"retrieved_documents": docs}

    except Exception as e:
        logger.error(f"[Knowledge Service] Exception: {e}")
        return {"retrieved_documents": []}

async def node_search_web(state: AgentState) -> dict:
    """
    并行节点：调用公网搜索 MCP
    """
    user_query = get_last_user_query(state)
    logger.info(f"[Web Search] Querying: {user_query}")

    try:
        mcp_client = get_search_mcp_client()
        result = await mcp_client.call_tool("bailian_web_search", {"query": user_query})
        logger.info(f"[Web Search] result: {result}")

        # 解析 MCP 返回的 TextContent
        content_text = result.content[0].text
        data = json.loads(content_text)

        results = data.get("pages", data.get("search_results", []))
        formatted_results = [
            {"source": "WebSearch", "content": r.get("snippet", r.get("content", "")), "title": r.get("title", "")}
            for r in results[:3]
        ]

        return {"retrieved_documents": formatted_results}
    except Exception as e:
        logger.error(f"[Web Search] MCP 服务异常: {type(e).__name__}: {e}")
        logger.warning("[Web Search] MCP 服务不可用，返回空结果（将触发人工升级）")
        return {"retrieved_documents": []}

async def node_query_local_tools(state: AgentState) -> dict:
    """
    并行节点：调用本地工具（服务站数据库、地图 API 等）
    """
    intent = state.get("current_intent")
    slots = state.get("slots", {})
    
    results = []
    
    if intent == "service_station":
        location_input = slots.get("location", "")
        logger.info(f"[Service Station] Resolving location: {location_input}")
        
        try:
            # 1. 解析坐标
            loc_res_str = await resolve_user_location_from_text_raw(user_input=location_input)
            loc_res = json.loads(loc_res_str)
            
            if loc_res.get("ok") or loc_res.get("source") == "fallback":
                lat = loc_res.get("lat")
                lng = loc_res.get("lng")
                
                # 2. 查询最近服务站
                shop_res_str = query_nearest_repair_shops_by_coords_raw(lat=lat, lng=lng)
                shop_res = json.loads(shop_res_str)
                
                if shop_res.get("ok"):
                    shops = shop_res.get("data", [])
                    for shop in shops:
                        content = f"服务站: {shop['service_station_name']}\n地址: {shop['address']}\n电话: {shop['phone']}\n距离: {shop['distance_km']:.2f}km"
                        results.append({"source": "LocalDB", "content": content, "metadata": shop})
            else:
                logger.warning(f"[Service Station] Location resolution failed: {loc_res.get('error')}")
        except Exception as e:
            logger.error(f"[Service Station] Exception: {e}")

    elif intent == "poi_navigation":
        destination = slots.get("destination", "")
        logger.info(f"[POI Navigation] Searching for: {destination}")
        try:
            baidu_client = get_baidu_mcp_client()
            res = await baidu_client.call_tool("map_poi_search", {"query": destination, "region": "全国"})
            data = json.loads(res.content[0].text)
            
            pois = data.get("results", [])
            for poi in pois[:3]:
                content = f"地点: {poi['name']}\n地址: {poi.get('address', '不详')}"
                results.append({"source": "BaiduMap", "content": content, "metadata": poi})
        except Exception as e:
            logger.info(f"[POI Navigation] Exception: {e}")

    return {"retrieved_documents": results}