"""
统一日志配置模块

功能：
1. 支持 traceId 追踪请求链路
2. 日志输出到文件（按日期轮转）
3. 使用 loguru 框架，简化日志配置
4. 支持结构化日志输出（JSON 格式）
5. 支持日志写入 Elasticsearch
"""

import sys
import contextvars
from pathlib import Path
from typing import Optional
from loguru import logger

# 使用 contextvars 存储 traceId（线程安全 + 协程安全）
trace_id_var = contextvars.ContextVar("trace_id", default="N/A")


def get_trace_id() -> str:
    """获取当前请求的 traceId"""
    return trace_id_var.get()


def set_trace_id(trace_id: str):
    """设置当前请求的 traceId"""
    trace_id_var.set(trace_id)


def format_record(record: dict) -> str:
    """
    自定义日志格式，注入 traceId

    格式: [时间] [级别] [traceId] [模块:行号] - 消息
    """
    trace_id = get_trace_id()

    # 彩色输出格式（控制台）
    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>traceId={extra[trace_id]}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )

    # 注入 traceId 到 extra 字段
    record["extra"]["trace_id"] = trace_id

    return format_string


def setup_logger(
    log_dir: str = "./logs",
    log_level: str = "INFO",
    rotation: str = "00:00",  # 每天午夜轮转
    retention: str = "30 days",  # 保留 30 天
    enable_json: bool = False,  # 是否启用 JSON 格式
    enable_es: bool = False,  # 是否启用 ES 输出
    es_client: Optional[object] = None,  # ES 客户端实例
    es_index_prefix: str = "app-logs"  # ES 索引前缀
):
    """
    配置全局日志

    Args:
        log_dir: 日志文件目录
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: 日志轮转策略 (时间或大小，如 "500 MB", "00:00")
        retention: 日志保留时间
        enable_json: 是否启用 JSON 格式（便于日志采集系统解析）
        enable_es: 是否启用 Elasticsearch 输出
        es_client: Elasticsearch 客户端实例
        es_index_prefix: ES 索引前缀（实际索引名：prefix-YYYY.MM.DD）
    """
    # 移除默认的 handler
    logger.remove()

    # 1. 控制台输出（彩色格式）
    logger.add(
        sys.stdout,
        format=format_record,
        level=log_level,
        colorize=True,
        backtrace=True,  # 显示完整的异常堆栈
        diagnose=True    # 显示变量值
    )

    # 2. 文件输出 - 普通日志（带颜色标记的文本格式）
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        format=format_record,
        level=log_level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )

    # 3. 文件输出 - 错误日志（单独记录 ERROR 及以上级别）
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        format=format_record,
        level="ERROR",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )

    # 4. JSON 格式日志（可选，便于 ELK/Loki 等日志系统采集）
    if enable_json:
        logger.add(
            log_path / "app_{time:YYYY-MM-DD}.json",
            format="{message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            serialize=True  # 输出为 JSON 格式
        )

    # 5. Elasticsearch 输出（可选，实时写入 ES）
    if enable_es and es_client:
        try:
            from infrastructure.es_logger_handler import ESLoggerHandler

            es_handler = ESLoggerHandler(
                es_client=es_client,
                index_prefix=es_index_prefix
            )

            logger.add(
                es_handler.write,
                format="{message}",
                level=log_level,
                serialize=True  # 输出 JSON 格式给 ES handler
            )

            logger.info(f"✅ ES 日志输出已启用 | 索引前缀: {es_index_prefix}")
        except Exception as e:
            logger.warning(f"⚠️ ES 日志输出启用失败: {e}")

    logger.info(f"✅ 日志系统初始化完成 | 日志目录: {log_path.absolute()} | 级别: {log_level}")


# 导出 logger 实例（其他模块直接 from infrastructure.logger import logger 使用）
__all__ = ["logger", "setup_logger", "get_trace_id", "set_trace_id"]
