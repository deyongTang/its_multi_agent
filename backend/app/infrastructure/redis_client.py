"""
Redis 客户端封装

提供 Redis 连接池和基础操作
"""
import redis
from typing import Optional
from config.settings import settings
from infrastructure.logging.logger import logger


class RedisClient:
    """Redis 客户端单例类"""

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        获取 Redis 客户端实例（单例模式）

        Returns:
            redis.Redis: Redis 客户端实例
        """
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    decode_responses=settings.REDIS_DECODE_RESPONSES,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                    # 连接池配置
                    max_connections=10,
                    health_check_interval=30,
                )
                # 测试连接
                cls._instance.ping()
                logger.info("Redis 客户端初始化成功")
            except Exception as e:
                logger.error(f"Redis 客户端初始化失败: {e}")
                raise

        return cls._instance

    @classmethod
    def close(cls):
        """关闭 Redis 连接"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis 连接已关闭")


# 全局 Redis 客户端实例
redis_client = RedisClient.get_client()
