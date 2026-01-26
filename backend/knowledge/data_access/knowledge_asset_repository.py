"""
知识资产表仓储层

负责 knowledge_asset 表的 CRUD 操作
"""
from typing import Optional, List, Dict
from datetime import datetime
from infrastructure.database import get_connection
import pymysql.cursors
from infrastructure.logger import logger



class KnowledgeAssetRepository:
    """知识资产表仓储"""

    @staticmethod
    def insert_or_update(
        knowledge_no: str,
        md_hash: str,
        oss_path: str,
        asset_uuid: str,
        source_update_time: Optional[datetime] = None
    ) -> bool:
        """
        插入或更新知识资产记录

        Args:
            knowledge_no: 知识编号
            md_hash: 内容哈希
            oss_path: OSS存储路径
            asset_uuid: 内部业务ID
            source_update_time: 源数据更新时间

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 如果记录存在，asset_uuid 保持不变（忽略传入的值），只更新内容相关字段
            sql = """
                INSERT INTO knowledge_asset
                (knowledge_no, asset_uuid, latest_hash, latest_oss_path, source_update_time, status)
                VALUES (%s, %s, %s, %s, %s, 'NEW')
                ON DUPLICATE KEY UPDATE
                    latest_hash = VALUES(latest_hash),
                    latest_oss_path = VALUES(latest_oss_path),
                    source_update_time = VALUES(source_update_time),
                    status = 'NEW',
                    updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(sql, (knowledge_no, asset_uuid, md_hash, oss_path, source_update_time))
            conn.commit()

            logger.info(f"知识资产记录已保存: {knowledge_no} (UUID: {asset_uuid})")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"插入/更新知识资产失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_by_knowledge_no(knowledge_no: str) -> Optional[Dict]:
        """
        根据知识编号查询资产记录
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            sql = """
                SELECT id, asset_uuid, knowledge_no, latest_hash, latest_oss_path, source_update_time,
                       status, chunks_count, error_message, retry_count,
                       updated_at, created_at
                FROM knowledge_asset
                WHERE knowledge_no = %s
            """

            cursor.execute(sql, (knowledge_no,))
            result = cursor.fetchone()

            return result

        except Exception as e:
            logger.error(f"查询知识资产失败: {str(e)}")
            return None

        finally:
            if conn:
                conn.close()

    @staticmethod
    def list_by_status(status: str, limit: int = 100) -> List[Dict]:
        """
        根据状态查询资产列表
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            sql = """
                SELECT id, asset_uuid, knowledge_no, latest_hash, latest_oss_path, source_update_time,
                       status, chunks_count, error_message, retry_count,
                       updated_at, created_at
                FROM knowledge_asset
                WHERE status = %s
                ORDER BY created_at ASC
                LIMIT %s
            """

            cursor.execute(sql, (status, limit))
            results = cursor.fetchall()

            return results

        except Exception as e:
            logger.error(f"查询知识资产列表失败: {str(e)}")
            return []

        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_status(
        asset_uuid: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新资产状态
        (使用内部 asset_uuid)

        Args:
            asset_uuid: 内部业务ID
            status: 新状态
            error_message: 错误信息 (可选)

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE knowledge_asset
                SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
                WHERE asset_uuid = %s
            """

            cursor.execute(sql, (status, error_message, asset_uuid))
            conn.commit()

            logger.info(f"知识资产状态已更新: {asset_uuid} -> {status}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"更新知识资产状态失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_chunks_count(asset_uuid: str, chunks_count: int) -> bool:
        """
        更新文档块数量
        (使用内部 asset_uuid)

        Args:
            asset_uuid: 内部业务ID
            chunks_count: 文档块数量

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE knowledge_asset
                SET chunks_count = %s, updated_at = CURRENT_TIMESTAMP
                WHERE asset_uuid = %s
            """

            cursor.execute(sql, (chunks_count, asset_uuid))
            conn.commit()

            logger.info(f"知识资产块数量已更新: {asset_uuid} -> {chunks_count}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"更新知识资产块数量失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def increment_retry_count(asset_uuid: str) -> bool:
        """
        增加重试次数
        (使用内部 asset_uuid)

        Args:
            asset_uuid: 内部业务ID

        Returns:
            bool: 操作是否成功
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                UPDATE knowledge_asset
                SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE asset_uuid = %s
            """

            cursor.execute(sql, (asset_uuid,))
            conn.commit()

            logger.info(f"知识资产重试次数已增加: {asset_uuid}")
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"增加知识资产重试次数失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()
