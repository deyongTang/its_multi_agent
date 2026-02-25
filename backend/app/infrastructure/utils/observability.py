"""
可观测性工具 (Observability Utilities)

- node_timer: 节点耗时装饰器，自动记录执行时间
"""
import time
from functools import wraps
from infrastructure.logging.logger import logger


def node_timer(node_name: str):
    """节点耗时装饰器，兼容同步和异步函数"""
    def decorator(fn):
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"[Timer] {node_name} 完成, 耗时 {elapsed:.0f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"[Timer] {node_name} 异常, 耗时 {elapsed:.0f}ms: {e}")
                raise

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"[Timer] {node_name} 完成, 耗时 {elapsed:.0f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"[Timer] {node_name} 异常, 耗时 {elapsed:.0f}ms: {e}")
                raise

        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    return decorator
