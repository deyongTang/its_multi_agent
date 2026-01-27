"""
用户认证 API 路由
提供注册、登录、Token 刷新等接口
"""
from fastapi import APIRouter, HTTPException, status, Depends
from schemas.schema import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse
)
from business_logic.auth_service import AuthService
from infrastructure.auth_dependencies import get_current_user
from infrastructure.logger import logger

# 创建认证路由
auth_router = APIRouter(prefix="/auth", tags=["认证"])

# 延迟初始化服务实例
_auth_service = None

def get_auth_service():
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


@auth_router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserRegister):
    """
    用户注册接口

    - **username**: 用户名 (唯一)
    - **email**: 邮箱 (唯一)
    - **password**: 密码
    """
    auth_service = get_auth_service()

    result = auth_service.register(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在或注册失败"
        )

    logger.info(f"新用户注册: {user_data.username}")
    return UserResponse(
        id=result["id"],
        username=result["username"],
        email=result["email"],
        is_active=True,
        created_at=result.get("created_at")
    )


@auth_router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(user_data: UserLogin):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码

    返回 access_token 和 refresh_token
    """
    auth_service = get_auth_service()

    result = auth_service.login(
        username=user_data.username,
        password=user_data.password
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(**result)


@auth_router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(token_data: TokenRefresh):
    """
    刷新 Access Token 接口

    - **refresh_token**: Refresh Token

    返回新的 access_token 和 refresh_token
    """
    auth_service = get_auth_service()

    result = auth_service.refresh_access_token(token_data.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(**result)


@auth_router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户信息

    需要在 Header 中携带有效的 Access Token:
    Authorization: Bearer <access_token>
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"]
    )
