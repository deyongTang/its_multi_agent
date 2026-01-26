"""
创建 Elasticsearch 日志索引模板

为日志索引定义 mapping，优化查询性能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.es_client import ESClient


def create_log_index_template():
    """创建日志索引模板"""

    es_client = ESClient()

    # 索引模板配置
    template_name = "app-logs-template"

    template_body = {
        "index_patterns": ["app-logs-*"],  # 匹配所有 app-logs-* 索引
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.refresh_interval": "5s"  # 5秒刷新一次
            },
            "mappings": {
                "properties": {
                    "@timestamp": {
                        "type": "date",
                        "format": "epoch_second"
                    },
                    "level": {
                        "type": "keyword"  # 日志级别：INFO, ERROR 等
                    },
                    "message": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "trace_id": {
                        "type": "keyword"  # 用于追踪请求链路
                    },
                    "module": {
                        "type": "keyword"  # 模块名
                    },
                    "function": {
                        "type": "keyword"  # 函数名
                    },
                    "line": {
                        "type": "integer"  # 行号
                    },
                    "file_path": {
                        "type": "keyword"  # 文件路径
                    },
                    "process_id": {
                        "type": "integer"
                    },
                    "thread_id": {
                        "type": "long"
                    },
                    "exception": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "keyword"},
                            "value": {"type": "text"},
                            "traceback": {"type": "text"}
                        }
                    }
                }
            }
        }
    }

    try:
        # 删除旧模板（如果存在）
        if es_client.client.indices.exists_index_template(name=template_name):
            es_client.client.indices.delete_index_template(name=template_name)
            print(f"🗑️  已删除旧模板: {template_name}")

        # 创建新模板
        es_client.client.indices.put_index_template(
            name=template_name,
            body=template_body
        )

        print(f"✅ 索引模板创建成功: {template_name}")
        print(f"📋 模板匹配模式: app-logs-*")

    except Exception as e:
        print(f"❌ 索引模板创建失败: {e}")


if __name__ == '__main__':
    create_log_index_template()
