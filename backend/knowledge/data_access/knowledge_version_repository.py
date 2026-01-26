"""
知识版本表仓储层

负责 knowledge_version 表的 CRUD 操作
"""
from typing import Optional, List, Dict
from datetime import datetime
from infrastructure.database import get_connection
import pymysql.cursors
from infrastructure.logger import logger



class KnowledgeVersionRepository:
    """知识版本表仓储"""

    @staticmethod
    def insert_version(
        knowledge_no: str,
        asset_uuid: str,
        md_hash: str,
        oss_path: str,
        source_update_time: Optional[datetime] = None
    ) -> int:
        """
        插入版本记录

        Args:
            knowledge_no: 知识编号
            asset_uuid: 内部业务ID
            md_hash: 内容哈希
            oss_path: OSS存储路径
            source_update_time: 源数据更新时间

        Returns:
            int: 插入的版本ID,失败返回 0
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO knowledge_version
                (knowledge_no, asset_uuid, md_hash, oss_path, source_update_time)
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (knowledge_no, asset_uuid, md_hash, oss_path, source_update_time))
            conn.commit()

            version_id = cursor.lastrowid
            logger.info(f"知识版本记录已插入: {knowledge_no} (UUID: {asset_uuid}, 版本ID: {version_id})")
            return version_id

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"插入知识版本失败: {str(e)}")
            return 0

        finally:
            if conn:
                conn.close()

    @staticmethod
    def version_exists(asset_uuid: str, md_hash: str) -> bool:
        """
        检查版本是否已存在 (幂等性检查)
        (使用内部 asset_uuid 查询)

        Args:
            asset_uuid: 内部业务ID
            md_hash: 内容哈希

        Returns:
            bool: 版本是否存在
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                SELECT 1
                FROM knowledge_version
                WHERE asset_uuid = %s AND md_hash = %s
                LIMIT 1
            """

            cursor.execute(sql, (asset_uuid, md_hash))
            result = cursor.fetchone()

            return result is not None

        except Exception as e:
            logger.error(f"检查知识版本是否存在失败: {str(e)}")
            return False

        finally:
            if conn:
                conn.close()

    @staticmethod
    def list_versions(asset_uuid: str, limit: int = 20) -> List[Dict]:
        """
        查询指定知识的所有版本
        (使用内部 asset_uuid 查询，并限制返回数量)

        Args:
            asset_uuid: 内部业务ID
            limit: 返回数量限制

        Returns:
            List[Dict]: 版本记录列表
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            sql = """
                SELECT id, asset_uuid, knowledge_no, md_hash, oss_path, source_update_time, created_at
                FROM knowledge_version
                WHERE asset_uuid = %s
                ORDER BY created_at DESC
                LIMIT %s
            """

            cursor.execute(sql, (asset_uuid, limit))
            results = cursor.fetchall()

            return results

        except Exception as e:
            logger.error(f"查询知识版本列表失败: {str(e)}")
            return []

        finally:
            if conn:
                conn.close()
