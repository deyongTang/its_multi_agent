#!/usr/bin/env python
"""测试导入顺序问题"""

print("=" * 60)
print("测试导入顺序")
print("=" * 60)

print("\n1. 导入 logger")
from infrastructure.logging.logger import logger

print("\n2. 导入 langsmith_client")
from infrastructure.observability.langsmith_client import langsmith_client

print("\n3. 初始化 langsmith_client")
try:
    langsmith_client.initialize()
    print("   ✅ LangSmith 初始化成功")
except Exception as e:
    print(f"   ❌ LangSmith 初始化失败: {e}")

print("\n4. 导入 mcp_manager")
try:
    from infrastructure.tools.mcp.mcp_manager import mcp_connect, mcp_cleanup
    print("   ✅ MCP Manager 导入成功")
except Exception as e:
    print(f"   ❌ MCP Manager 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n5. 导入 router")
try:
    from api.routers import router
    print("   ✅ Router 导入成功")
except Exception as e:
    print(f"   ❌ Router 导入失败: {e}")

print("\n" + "=" * 60)
print("导入测试完成")
print("=" * 60)
