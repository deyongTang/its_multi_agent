from infrastructure.database.database_pool import pool
import json
import stun
from pymysql.cursors import DictCursor
from infrastructure.tools.mcp.mcp_servers import create_baidu_mcp_client
from infrastructure.logging.logger import logger
import math


def bd09mc_to_bd09(lng: float, lat: float) -> tuple[float, float]:
    """
    [工具函数] 百度墨卡托坐标 (BD09MC) 转 百度经纬度 (BD09)
    百度地图 IP 定位 API 返回的是墨卡托坐标，导航 API 需要经纬度，因此必须转换。
    来源：https://github.com/wandergis/coordTransform_py/blob/master/coordTransform_utils.py
    """
    x = lng
    y = lat

    # 1. 简单校验：如果坐标值过小，视为无效坐标（通常在中国境外或解析错误）
    if abs(y) < 1e-6 or abs(x) < 1e-6:
        return (0.0, 0.0)

    # 2. 核心算法：墨卡托平面坐标转球面经纬度
    lng = x / 20037508.34 * 180
    lat = y / 20037508.34 * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)

    return (lng, lat)


def get_ip_via_stun():
    """
        [辅助函数] 获取本机公网 IP
        注意：在服务器部署时，这获取的是服务器机房 IP。
        如果要获取终端用户 IP，建议使用 ContextVars 从 HTTP Header 中透传。
        真正开发期间--->前端请求的时候携带过来---->FastAPI的request携带过来---注入到工具中，工具使用。
    """

    try:
        # 默认使用公用的 STUN 服务器
        nat_type, external_ip, external_port = stun.get_ip_info()
        return external_ip
    except Exception as e:
        print(f"STUN 获取失败: {e}")
        return None

async def resolve_user_location_from_text_raw(
        user_input: str,
) -> str:
    """
    智能解析用户当前位置（起点），用于导航或服务站查询。
    ⚠️ 注意：
    - 仅用于获取**起点**，不可作为终点使用。

    Args:
        user_input (str): 用户提到的**明确地名**。⚠️重要：如果用户只说了“附近”、“这里”、“我的位置”等相对方位词，请**留空**此参数（传空字符串），不要填入这些词。

    返回 JSON 字符串：
    {
        "ok": bool,
        "lat": float,
        "lng": float,
        "source": "geocode" | "ip" | "fallback",
        "original_input": str,
        "error": str?  # 仅当 ok=False 时存在
    }
    """

    # 1. 相对位置词黑名单 ---
    RELATIVE_LOCATIONS = {
        "附近", "这", "这里", "这儿", "周围", "周边",
        "我的位置", "当前位置", "所在位置", "nearby", "here"
    }

    user_input = user_input.strip() if user_input else ""

    if user_input in RELATIVE_LOCATIONS:
        logger.info(f"[Location] Detected relative term '{user_input}', forcing IP location fallback.")
        user_input = ""

    if user_input:
        try:
            async with create_baidu_mcp_client() as baidu_client:
                geo_result = await baidu_client.call_tool(tool_name="map_geocode", arguments={"address": user_input})
            text = geo_result.content[0].text
            text = json.loads(text)
            result = text['result']

            if isinstance(result, dict) and "lat" in result['location'] and "lng" in result['location']:
                lat = float(result['location']['lat'])
                lng = float(result['location']['lng'])
                logger.info(f"[Location] Geocode success: '{user_input}' → ({lat}, {lng})")
                return json.dumps({
                    "ok": True,
                    "lat": lat,
                    "lng": lng,
                    "source": "geocode"
                }, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[Location] Geocode failed for '{user_input}': {e}")

    user_ip = get_ip_via_stun()

    if user_ip and user_ip not in ("127.0.0.1", "localhost", "::1"):
        try:
            async with create_baidu_mcp_client() as baidu_client:
                ip_result = await baidu_client.call_tool("map_ip_location", {"ip": user_ip})
            text = ip_result.content[0].text
            data = json.loads(text)

            if data.get("status") == 0:
                point = data.get("content", {}).get("point", {})
                x = float(point.get("x"))
                y = float(point.get("y"))
                lng, lat = bd09mc_to_bd09(x, y)

                logger.info(f"[Location] IP location success: {user_ip} → ({lat:.6f}, {lng:.6f})")
                return json.dumps({
                    "ok": True,
                    "lat": lat,
                    "lng": lng,
                    "source": "ip"
                }, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[Location] IP location failed for {user_ip}: {e}")

    fallback_lat, fallback_lng = 39.9042, 116.4074
    logger.info("[Location] Using fallback coordinates (Beijing)")

    return json.dumps({
        "ok": False,
        "error": "无法解析用户位置，使用默认坐标",
        "lat": fallback_lat,
        "lng": fallback_lng,
        "source": "fallback"
    }, ensure_ascii=False)


def query_nearest_repair_shops_by_coords_raw(lat: float, lng: float, limit: int = 3) -> str:
    """
    根据给定的经纬度坐标，查询数据库中最近的维修站/服务站。

    Args:
        lat (float): 纬度 (BD09LL)
        lng (float): 经度 (BD09LL)
        limit (int): 返回结果数量限制，默认为 3

    Returns:
        str: JSON 格式的查询结果，包含最近的维修站列表。
    """
    connection = None
    cursor = None
    try:
        connection = pool.connection()
        cursor = connection.cursor(DictCursor)

        sql = """
        SELECT
            id, service_station_name, address, phone, latitude, longitude,
            (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
        FROM repair_shops
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY distance_km ASC
        LIMIT %s
        """
        cursor.execute(sql, (lat, lng, lat, limit))
        rows = cursor.fetchall()
        return json.dumps({"ok": True, "count": len(rows), "data": rows}, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"[NearestShops] DB query failed: {e}")
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
    finally:
        if cursor: cursor.close()
        if connection: connection.close()