"""
用户认证业务逻辑层
负责用户注册、登录、Token 生成等业务逻辑
"""
from typing import Optional, Dict
from data_access.user_repository import UserRepository
from utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from infrastructure.logger import logger


class AuthService:
    """用户认证服务类"""

    def __init__(self):
        self.user_repo = UserRepository()

    def register(self, username: str, email: str, password: str) -> Optional[Dict]:
        """
        用户注册

        Args:
            username: 用户名
            email: 邮箱
            password: 明文密码

        Returns:
            注册成功返回用户信息,失败返回 None
        """
        # 检查用户名是否已存在
        existing_user = self.user_repo.get_user_by_username(username)
        if existing_user:
            logger.warning(f"用户名已存在: {username}")
            return None

        # 加密密码
        hashed_password = hash_password(password)

        # 创建用户
        user_id = self.user_repo.create_user(username, email, hashed_password)
        if not user_id:
            return None

        return {
            "id": user_id,
            "username": username,
            "email": email
        }

    def login(self, username: str, password: str) -> Optional[Dict]:
        """
        用户登录

        Args:
            username: 用户名
            password: 明文密码

        Returns:
            登录成功返回 tokens,失败返回 None
        """
        # 查询用户
        user = self.user_repo.get_user_by_username(username)
        if not user:
            logger.warning(f"用户不存在: {username}")
            return None

        # 验证密码
        if not verify_password(password, user["hashed_password"]):
            logger.warning(f"密码错误: {username}")
            return None

        # 检查用户是否激活
        if not user["is_active"]:
            logger.warning(f"用户已被禁用: {username}")
            return None

        # 生成 tokens
        token_data = {"user_id": user["id"], "username": user["username"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        logger.info(f"用户登录成功: {username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        刷新 Access Token

        Args:
            refresh_token: Refresh Token

        Returns:
            新的 tokens,失败返回 None
        """
        from utils.security import decode_token

        # 解码 refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            logger.warning("无效的 refresh token")
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        # 查询用户
        user = self.user_repo.get_user_by_id(user_id)
        if not user or not user["is_active"]:
            return None

        # 生成新的 tokens
        token_data = {"user_id": user["id"], "username": user["username"]}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
