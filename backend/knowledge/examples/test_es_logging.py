"""
测试日志写入 Elasticsearch

验证日志系统是否能正确写入 ES
"""

import sys
from pathlib import Path
import time

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.logger import logger, setup_logger, set_trace_id
from infrastructure.es_client import ESClient
import uuid


def test_es_logging():
    """测试 ES 日志写入"""

    print("=" * 60)
    print("开始测试日志写入 Elasticsearch")
    print("=" * 60)

    # 1. 初始化 ES 客户端
    print("\n📡 步骤 1: 连接 Elasticsearch...")
    try:
        es_client = ESClient()
        print("✅ ES 连接成功")
    except Exception as e:
        print(f"❌ ES 连接失败: {e}")
        return

    # 2. 初始化日志系统（启用 ES 输出）
    print("\n📝 步骤 2: 初始化日志系统...")
    setup_logger(
        log_dir="./logs",
        log_level="INFO",
        enable_es=True,  # 启用 ES 输出
        es_client=es_client.client,
        es_index_prefix="app-logs"
    )

    # 3. 生成测试日志
    print("\n🧪 步骤 3: 生成测试日志...")

    # 设置 traceId
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("🚀 这是一条测试日志 - INFO 级别")
    logger.warning("⚠️ 这是一条警告日志 - WARNING 级别")
    logger.error("❌ 这是一条错误日志 - ERROR 级别")

    # 测试带变量的日志
    user_id = 12345
    action = "测试操作"
    logger.info(f"👤 用户操作 | ID: {user_id} | 操作: {action}")

    # 测试异常日志
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception(f"💥 捕获异常: {e}")

    print("✅ 测试日志已生成")

    # 4. 等待 ES 刷新
    print("\n⏳ 步骤 4: 等待 ES 索引刷新（5秒）...")
    time.sleep(6)

    # 5. 查询验证
    print("\n🔍 步骤 5: 查询 ES 验证日志...")
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y.%m.%d")
        index_name = f"app-logs-{today}"

        # 查询今天的日志
        query = {
            "query": {
                "match": {
                    "trace_id": trace_id
                }
            },
            "size": 10,
            "sort": [{"@timestamp": "desc"}]
        }

        results = es_client.search(index_name=index_name, query=query)

        # ES 返回格式：{'hits': {'hits': [{'_source': {...}}]}}
        if results and 'hits' in results and 'hits' in results['hits']:
            hits = results['hits']['hits']
            print(f"✅ 成功查询到 {len(hits)} 条日志")
            print("\n📋 日志详情:")
            for i, hit in enumerate(hits, 1):
                source = hit.get('_source', {})
                level = source.get('level', 'N/A')
                message = source.get('message', 'N/A')
                trace_id_short = source.get('trace_id', 'N/A')[:8]
                message_preview = message[:50] if len(message) > 50 else message
                print(f"\n  [{i}] 级别: {level} | TraceId: {trace_id_short}... | 消息: {message_preview}...")
        else:
            print("⚠️ 未查询到日志，可能需要等待更长时间")

    except Exception as e:
        print(f"❌ 查询失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    test_es_logging()
