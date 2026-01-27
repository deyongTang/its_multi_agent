"""
用户数据访问层
负责用户相关的数据库操作
"""
from typing import Optional, Dict
from infrastructure.database import get_connection
from infrastructure.logger import logger


class UserRepository:
    """用户数据访问类"""

    def create_user(self, username: str, email: str, hashed_password: str) -> Optional[int]:
        """
        创建新用户

        Args:
            username: 用户名
            email: 邮箱
            hashed_password: 加密后的密码

        Returns:
            新创建用户的 ID,失败返回 None
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                INSERT INTO users (username, email, hashed_password, is_active)
                VALUES (%s, %s, %s, 1)
            """
            cursor.execute(sql, (username, email, hashed_password))
            conn.commit()

            user_id = cursor.lastrowid
            logger.info(f"用户创建成功: {username} (ID: {user_id})")
            return user_id

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"创建用户失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        根据用户名查询用户

        Args:
            username: 用户名

        Returns:
            用户信息字典,不存在返回 None
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                SELECT id, username, email, hashed_password, is_active, created_at
                FROM users
                WHERE username = %s
            """
            cursor.execute(sql, (username,))
            result = cursor.fetchone()

            if result:
                return {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "hashed_password": result[3],
                    "is_active": result[4],
                    "created_at": result[5]
                }
            return None

        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        根据用户 ID 查询用户

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典,不存在返回 None
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sql = """
                SELECT id, username, email, hashed_password, is_active, created_at
                FROM users
                WHERE id = %s
            """
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()

            if result:
                return {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "hashed_password": result[3],
                    "is_active": result[4],
                    "created_at": result[5]
                }
            return None

        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
        finally:
            if conn:
                conn.close()
