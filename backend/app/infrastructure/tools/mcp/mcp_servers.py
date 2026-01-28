import asyncio
import json
from agents.mcp import MCPServerSse
from typing import Dict, Any, Optional

# 延迟初始化 MCP 客户端，避免导入时的配置加载问题
_search_mcp_client: Optional[MCPServerSse] = None
_baidu_mcp_client: Optional[MCPServerSse] = None


def get_search_mcp_client() -> MCPServerSse:
    """
    延迟初始化搜索 MCP 客户端

    只在第一次调用时创建客户端实例，确保 settings 已经完全加载
    """
    global _search_mcp_client
    if _search_mcp_client is None:
        from config.settings import settings
        _search_mcp_client = MCPServerSse(
            name="通用联网搜索",
            params={
                "url": settings.DASHSCOPE_BASE_URL,
                "headers": {
                    "Authorization": f"Bearer {settings.AL_BAILIAN_API_KEY}"
                },
                "timeout": 60,
                "sse_read_timeout": 60 * 30
            },
            client_session_timeout_seconds=60 * 10,
            cache_tools_list=True,
        )
    return _search_mcp_client


def get_baidu_mcp_client() -> MCPServerSse:
    """
    延迟初始化百度地图 MCP 客户端

    只在第一次调用时创建客户端实例，确保 settings 已经完全加载
    """
    global _baidu_mcp_client
    if _baidu_mcp_client is None:
        from config.settings import settings
        _baidu_mcp_client = MCPServerSse(
            name="百度地图",
            params={
                "url": f"https://mcp.map.baidu.com/sse?ak={settings.BAIDUMAP_AK}",
                "timeout": 60,
                "sse_read_timeout": 60 * 30
            },
            client_session_timeout_seconds=60 * 10,
            cache_tools_list=True,
        )
    return _baidu_mcp_client


# 为了保持向后兼容，提供旧的变量名（但实际是函数调用）
# 注意：这些不再是全局变量，而是函数引用
search_mcp_client = get_search_mcp_client
baidu_mcp_client = get_baidu_mcp_client
