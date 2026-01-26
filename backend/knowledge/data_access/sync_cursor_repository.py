"""
同步游标表仓储层

负责 sync_cursor 表的 CRUD 操作
"""
from typing import Optional, Dict
from infrastructure.database import get_connection
import pymysql.cursors
from infrastructure.logger import logger



class SyncCursorRepository:
    """同步游标表仓储"""

    @staticmethod
    def get_cursor(sync_type: str) -> Optional[Dict]:
        """
        获取同步游标记录

        Args:
            sync_type: 同步类型 (FULL/INCR)

        Returns:
            Optional[Dict]: 游标记录,不存在则返回 None
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            sql = """
                SELECT id, sync_type, last_cursor, last_sync_time, sync_status,
                       total_processed, total_updated, total_skipped, total_failed,
                       error_message
                FROM sync_cursor
                WHERE sync_type = %s
                ORDER BY id DESC
                LIMIT 1
            """

            cursor.execute(sql, (sync_type,))
            result = cursor.fetchone()

            return result

        except Exception as e:
            logger.error(f"查询同步游标失败: {str(e)}")
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def start_sync(sync_type: str) -> bool:
        """
        开始同步 (设置状态为 RUNNING)

        Args:
            sync_type: 同步类型 (FULL/INCR)

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO sync_cursor (sync_type, sync_status, last_sync_time)
                VALUES (%s, 'RUNNING', NOW())
            """

            cursor.execute(sql, (sync_type,))
            conn.commit()

            logger.info(f"同步已开始: {sync_type}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"开始同步失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def complete_sync(
        sync_type: str,
        last_cursor: Optional[str],
        stats: Dict
    ) -> bool:
        """
        完成同步 (设置状态为 SUCCESS)

        Args:
            sync_type: 同步类型
            last_cursor: 最后同步游标
            stats: 统计信息 {processed, updated, skipped, failed}

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE sync_cursor
                SET sync_status = 'SUCCESS',
                    last_cursor = %s,
                    last_sync_time = NOW(),
                    total_processed = %s,
                    total_updated = %s,
                    total_skipped = %s,
                    total_failed = %s
                WHERE sync_type = %s
                ORDER BY id DESC
                LIMIT 1
            """

            cursor.execute(sql, (
                last_cursor,
                stats.get('processed', 0),
                stats.get('updated', 0),
                stats.get('skipped', 0),
                stats.get('failed', 0),
                sync_type
            ))
            conn.commit()

            logger.info(f"同步已完成: {sync_type}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"完成同步失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def fail_sync(sync_type: str, error_message: str) -> bool:
        """
        同步失败 (设置状态为 FAILED)

        Args:
            sync_type: 同步类型
            error_message: 错误信息

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE sync_cursor
                SET sync_status = 'FAILED',
                    error_message = %s,
                    last_sync_time = NOW()
                WHERE sync_type = %s
                ORDER BY id DESC
                LIMIT 1
            """

            cursor.execute(sql, (error_message, sync_type))
            conn.commit()

            logger.error(f"同步失败: {sync_type} - {error_message}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"记录同步失败状态失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()
