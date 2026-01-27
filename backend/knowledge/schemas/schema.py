from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ==================== 用户认证相关 Schema ====================

class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token 响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token 刷新请求模型"""
    refresh_token: str


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


# ==================== 知识库相关 Schema ====================

class UploadResponse(BaseModel):
    """
     文件上传的响应数据模型
    """
    status:str  # 响应状态
    message:str # 响应的消息内容
    file_name:str # 上传的文件名
    chunks_added:int # 上传文档切分之后的文档块数量


class QueryRequest(BaseModel):
    """
    知识库查询的请求数据模型
    """
    question: str  # 用户提出的问题


class QueryResponse(BaseModel):
    """
    知识库查询的响应数据模型
    """
    question: str  # 用户提出的问题
    answer: str  # 生成的答案


