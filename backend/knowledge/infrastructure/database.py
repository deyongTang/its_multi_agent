"""
数据库连接池管理模块

使用 pymysql + DBUtils.PooledDB 创建 MySQL 连接池
"""
import pymysql
from dbutils.pooled_db import PooledDB
from config.settings import settings
from infrastructure.logger import logger



class DatabaseManager:
    """数据库连接池管理器"""

    _pool = None

    @classmethod
    def get_pool(cls):
        """获取数据库连接池实例 (单例模式)"""
        if cls._pool is None:
            try:
                cls._pool = PooledDB(
                    creator=pymysql,
                    maxconnections=10,  # 最大连接数
                    mincached=2,        # 初始化时至少创建的空闲连接
                    maxcached=5,        # 连接池中最多闲置的连接数
                    maxshared=3,        # 最多共享的连接数
                    blocking=True,      # 连接池中如果没有可用连接是否阻塞等待
                    maxusage=None,      # 单个连接最多被重复使用的次数
                    setsession=[],      # 开始会话前执行的命令列表
                    ping=1,             # ping MySQL服务端,检查是否服务可用
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    database=settings.DB_NAME,
                    charset='utf8mb4'
                )
                logger.info(f"数据库连接池初始化成功: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
            except Exception as e:
                logger.error(f"数据库连接池初始化失败: {str(e)}")
                raise e

        return cls._pool

    @classmethod
    def get_connection(cls):
        """从连接池获取一个数据库连接"""
        pool = cls.get_pool()
        return pool.connection()


def get_connection():
    """便捷函数: 获取数据库连接"""
    return DatabaseManager.get_connection()
