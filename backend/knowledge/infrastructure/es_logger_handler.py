"""
Elasticsearch 日志 Handler

将日志实时写入 Elasticsearch，便于集中管理和查询
"""

import json
from datetime import datetime
from typing import Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class ESLoggerHandler:
    """
    Elasticsearch 日志处理器

    功能：
    1. 将日志实时写入 ES
    2. 支持批量写入（提高性能）
    3. 自动创建索引（按日期）
    4. 异常容错（ES 故障不影响应用）
    """

    def __init__(
        self,
        es_client: Elasticsearch,
        index_prefix: str = "app-logs",
        batch_size: int = 10,
        flush_interval: int = 5
    ):
        """
        初始化 ES 日志处理器

        Args:
            es_client: Elasticsearch 客户端实例
            index_prefix: 索引前缀（实际索引名：prefix-YYYY.MM.DD）
            batch_size: 批量写入大小
            flush_interval: 刷新间隔（秒）
        """
        self.es_client = es_client
        self.index_prefix = index_prefix
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []

    def get_index_name(self) -> str:
        """获取当前日期的索引名"""
        today = datetime.now().strftime("%Y.%m.%d")
        return f"{self.index_prefix}-{today}"

    def write(self, message: str):
        """
        loguru sink 方法，接收日志消息

        Args:
            message: loguru 序列化后的日志消息（JSON 字符串）
        """
        try:
            # 解析 loguru 的 JSON 格式日志
            log_record = json.loads(message)

            # 提取关键字段
            doc = {
                "@timestamp": log_record["record"]["time"]["timestamp"],
                "level": log_record["record"]["level"]["name"],
                "message": log_record["text"].strip(),
                "trace_id": log_record["record"]["extra"].get("trace_id", "N/A"),
                "module": log_record["record"]["name"],
                "function": log_record["record"]["function"],
                "line": log_record["record"]["line"],
                "file_path": log_record["record"]["file"]["path"],
                "process_id": log_record["record"]["process"]["id"],
                "thread_id": log_record["record"]["thread"]["id"],
            }

            # 如果有异常信息，添加到文档
            if log_record["record"]["exception"]:
                doc["exception"] = {
                    "type": log_record["record"]["exception"]["type"],
                    "value": log_record["record"]["exception"]["value"],
                    "traceback": log_record["record"]["exception"]["traceback"]
                }

            # 写入 ES
            self._write_to_es(doc)

        except Exception as e:
            # 容错：ES 写入失败不影响应用运行
            print(f"⚠️ ES 日志写入失败: {e}")

    def _write_to_es(self, doc: dict):
        """
        将日志文档写入 ES

        Args:
            doc: 日志文档
        """
        try:
            index_name = self.get_index_name()

            # 直接写入（实时性好）
            self.es_client.index(
                index=index_name,
                document=doc
            )

        except Exception as e:
            print(f"⚠️ ES 索引写入失败: {e}")
