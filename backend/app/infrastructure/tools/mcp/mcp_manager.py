from infrastructure.logging.logger import logger
from infrastructure.tools.mcp.mcp_servers import (
    get_search_mcp_client,
    get_baidu_mcp_client,
)

async def mcp_connect():
    """
    建立MCP连接

    在运行时调用 getter 函数来获取客户端实例，
    确保 settings 已经完全加载
    """
    try:
        baidu_client = get_baidu_mcp_client()
        await baidu_client.connect()
    except Exception as e:
        logger.error(f"百度地图MCP连接失败: {str(e)}")
    try:
        search_client = get_search_mcp_client()
        await search_client.connect()
    except Exception as e:
        logger.error(f"搜索MCP连接失败: {str(e)}")


async def mcp_cleanup():
    """
    清理MCP连接

    在运行时调用 getter 函数来获取客户端实例
    """
    try:
        baidu_client = get_baidu_mcp_client()
        await baidu_client.cleanup()
    except Exception as e:
        logger.warning(f"百度地图MCP清理时出现非致命错误: {e}")
    try:
        search_client = get_search_mcp_client()
        await search_client.cleanup()
    except Exception as e:
        logger.warning(f"搜索MCP清理时出现非致命错误: {e}")