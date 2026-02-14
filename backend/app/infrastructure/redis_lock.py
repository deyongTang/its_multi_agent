"""
Redis 分布式锁实现

基于 Redis 的 SET NX EX 命令实现分布式锁，防止并发写入导致数据乱序
"""
import time
import uuid
from typing import Optional
from contextlib import contextmanager
from infrastructure.redis_client import redis_client
from infrastructure.logging.logger import logger


class RedisLock:
    """Redis 分布式锁"""

    def __init__(self, lock_key: str, timeout: int = 5, retry_times: int = 3, retry_delay: float = 0.1):
        """
        初始化分布式锁

        Args:
            lock_key: 锁的键名
            timeout: 锁的超时时间（秒），防止死锁
            retry_times: 获取锁失败时的重试次数
            retry_delay: 重试间隔（秒）
        """
        self.lock_key = lock_key
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.lock_value = str(uuid.uuid4())  # 唯一标识，防止误删其他进程的锁

    def acquire(self) -> bool:
        """
        获取锁

        Returns:
            bool: 是否成功获取锁
        """
        for attempt in range(self.retry_times):
            # 使用 SET NX EX 原子操作
            success = redis_client.set(
                self.lock_key,
                self.lock_value,
                nx=True,  # 只在键不存在时设置
                ex=self.timeout  # 设置过期时间
            )

            if success:
                logger.debug(f"成功获取锁: {self.lock_key}")
                return True

            # 获取失败，等待后重试
            if attempt < self.retry_times - 1:
                logger.debug(f"获取锁失败，{self.retry_delay}秒后重试 ({attempt + 1}/{self.retry_times})")
                time.sleep(self.retry_delay)

        logger.warning(f"获取锁失败，已重试 {self.retry_times} 次: {self.lock_key}")
        return False

    def release(self):
        """
        释放锁（使用 Lua 脚本保证原子性）
        """
        # Lua 脚本：只有当锁的值匹配时才删除（防止误删其他进程的锁）
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = redis_client.eval(lua_script, 1, self.lock_key, self.lock_value)
            if result:
                logger.debug(f"成功释放锁: {self.lock_key}")
            else:
                logger.warning(f"锁已过期或被其他进程持有: {self.lock_key}")
        except Exception as e:
            logger.error(f"释放锁异常: {e}")


@contextmanager
def redis_lock(lock_key: str, timeout: int = 5, retry_times: int = 3, retry_delay: float = 0.1):
    """
    Redis 分布式锁上下文管理器

    使用示例:
        with redis_lock(f"lock:session:{session_id}:write", timeout=5):
            # 临界区代码
            history = db.get_history(session_id)
            history.append(new_msg)
            db.save_history(session_id, history)

    Args:
        lock_key: 锁的键名
        timeout: 锁的超时时间（秒）
        retry_times: 获取锁失败时的重试次数
        retry_delay: 重试间隔（秒）

    Raises:
        RuntimeError: 获取锁失败时抛出异常
    """
    lock = RedisLock(lock_key, timeout, retry_times, retry_delay)

    # 获取锁
    if not lock.acquire():
        raise RuntimeError(f"无法获取分布式锁: {lock_key}")

    try:
        yield lock
    finally:
        # 释放锁
        lock.release()
