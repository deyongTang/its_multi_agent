async def mcp_connect():
    """MCP 连接现在由各调用方用 async with 按需建立，无需全局预连接"""
    pass


async def mcp_cleanup():
    """MCP 连接现在由各调用方用 async with 自动释放，无需全局清理"""
    pass
