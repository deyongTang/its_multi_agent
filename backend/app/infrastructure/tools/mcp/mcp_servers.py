from agents.mcp import MCPServerSse


def create_search_mcp_client() -> MCPServerSse:
    """每次调用返回一个新的搜索 MCP 客户端实例，用 async with 管理生命周期"""
    from config.settings import settings
    return MCPServerSse(
        name="通用联网搜索",
        params={
            "url": settings.DASHSCOPE_BASE_URL,
            "headers": {
                "Authorization": f"Bearer {settings.AL_BAILIAN_API_KEY}"
            },
            "timeout": 60,
            "sse_read_timeout": 60 * 5
        },
        client_session_timeout_seconds=60 * 5,
        cache_tools_list=True,
    )


def create_baidu_mcp_client() -> MCPServerSse:
    """每次调用返回一个新的百度地图 MCP 客户端实例，用 async with 管理生命周期"""
    from config.settings import settings
    return MCPServerSse(
        name="百度地图",
        params={
            "url": f"https://mcp.map.baidu.com/sse?ak={settings.BAIDUMAP_AK}",
            "timeout": 60,
            "sse_read_timeout": 60 * 5
        },
        client_session_timeout_seconds=60 * 5,
        cache_tools_list=True,
    )
