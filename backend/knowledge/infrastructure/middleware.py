"""
FastAPI 中间件

功能：
1. 自动为每个请求生成 traceId
2. 将 traceId 注入到日志上下文
3. 在响应头中返回 traceId（便于前端追踪）
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from infrastructure.logger import set_trace_id, logger


class TraceIdMiddleware(BaseHTTPMiddleware):
    """
    TraceId 中间件

    为每个请求生成唯一的 traceId，并注入到日志上下文中
    """

    async def dispatch(self, request: Request, call_next):
        # 1. 生成或获取 traceId
        # 优先从请求头获取（支持分布式链路追踪）
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())

        # 2. 将 traceId 注入到日志上下文
        set_trace_id(trace_id)

        # 3. 记录请求开始
        logger.info(
            f"📥 请求开始 | 方法: {request.method} | 路径: {request.url.path} | "
            f"客户端: {request.client.host if request.client else 'unknown'}"
        )

        # 4. 执行请求处理
        try:
            response = await call_next(request)

            # 5. 在响应头中返回 traceId
            response.headers["X-Trace-Id"] = trace_id

            # 6. 记录请求完成
            logger.info(
                f"📤 请求完成 | 状态码: {response.status_code} | "
                f"方法: {request.method} | 路径: {request.url.path}"
            )

            return response

        except Exception as e:
            # 7. 记录请求异常
            logger.error(
                f"❌ 请求异常 | 方法: {request.method} | 路径: {request.url.path} | "
                f"错误: {str(e)}"
            )
            raise
