import asyncio
import json
from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger 
from infrastructure.tools.local.knowledge_base import query_knowledge_raw
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
    并行节点：调用知识库平台 HTTP API
    """
    user_query = get_last_user_query(state)
    logger.info(f"[Knowledge Service] Querying: {user_query}")

    try:
        result = await query_knowledge_raw(question=user_query)
        
        if result.get("status") == "error":
            logger.warning(f"[Knowledge Service] API Error: {result.get('error_msg')}")
            return {"retrieved_documents": []}
            
        answer = result.get("answer", "").strip()
        
        # --- 核心修复：有效性校验 ---
        # 如果知识库明确表示没找到，视为无结果，强制返回空列表以触发兜底
        invalid_patterns = ["未找到", "没有找到", "抱歉", "无法回答", "No result", "I don't know"]
        is_invalid = not answer or any(p in answer for p in invalid_patterns)
        
        if is_invalid:
            logger.info(f"[Knowledge Service] 结果被判定为无效/拒答，准备触发兜底。Answer: {answer[:20]}...")
            return {"retrieved_documents": []}
            
        return {"retrieved_documents": [{"source": "KnowledgeBase", "content": answer, "metadata": result}]}
        
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
        result = await mcp_client.call_tool("web_search", {"query": user_query})
        
        # 解析 MCP 返回的 TextContent
        content_text = result.content[0].text
        data = json.loads(content_text)
        
        results = data.get("search_results", [])
        formatted_results = [
            {"source": "WebSearch", "content": r.get("content", ""), "title": r.get("title", "")}
            for r in results[:3]
        ]
        
        return {"retrieved_documents": formatted_results}
    except Exception as e:
        logger.error(f"[Web Search] Exception: {e}")
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