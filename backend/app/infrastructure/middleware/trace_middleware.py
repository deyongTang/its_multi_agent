import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from infrastructure.logging.logger import trace_id_var


class TraceIdMiddleware(BaseHTTPMiddleware):
    """
    TraceId 中间件

    为每个 HTTP 请求自动生成唯一的 traceId，并设置到上下文变量中
    这样所有日志都会自动包含 traceId，无需在业务代码中手动设置
    """

    async def dispatch(self, request: Request, call_next):
        # 1. 生成唯一的 traceId（8位短ID）
        trace_id = str(uuid.uuid4())[:8]

        # 2. 设置到上下文变量（所有后续日志都会自动包含）
        trace_id_var.set(trace_id)

        # 3. 可选：将 traceId 添加到请求头，方便前端获取
        request.state.trace_id = trace_id

        # 4. 执行请求处理
        response = await call_next(request)

        # 5. 可选：将 traceId 添加到响应头，方便前端追踪
        response.headers["X-Trace-Id"] = trace_id

        return response
