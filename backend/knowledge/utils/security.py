"""
安全工具模块
提供密码加密、JWT token 生成和验证功能
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from config.settings import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    对密码进行哈希加密

    Args:
        password: 明文密码

    Returns:
        加密后的密码哈希值
    """
    # bcrypt 限制密码最长 72 字节，需要截断
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确

    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码哈希值

    Returns:
        密码是否匹配
    """
    # bcrypt 限制密码最长 72 字节，需要截断
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes, hashed_password)


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Access Token

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """
    创建 JWT Refresh Token

    Args:
        data: 要编码到 token 中的数据

    Returns:
        JWT refresh token 字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """
    解码并验证 JWT Token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload 数据,如果验证失败则返回 None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:  # Fixed: JWTError -> PyJWTError for PyJWT library
        return None
