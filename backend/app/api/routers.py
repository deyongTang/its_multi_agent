from fastapi.routing import APIRouter
from starlette.responses import StreamingResponse

from schemas.request import ChatMessageRequest, UserSessionsRequest
# from services.agent_service import MultiAgentService  # V1 已废弃
from services.agent_service_v2 import MultiAgentServiceV2
from infrastructure.logging.logger import logger
from services.session_service import session_service

# 1. 定义请求路由器
router = APIRouter()


# 2. 定义对话请求 (V1 - 旧版 Orchestrator) - 已废弃，使用 V2
@router.post("/api/query", summary="智能体对话接口 (V2 - LangGraph)")
async def query(request_context: ChatMessageRequest) -> StreamingResponse:
    """
    LangGraph 引擎对话接口（主接口）
    """
    user_id = request_context.context.user_id
    user_query = request_context.query
    logger.info(f"用户 {user_id} 发送任务: {user_query}")

    # 使用 V2 LangGraph 引擎
    async_generator_result = MultiAgentServiceV2.process_task(request_context, flag=True)

    return StreamingResponse(
        content=async_generator_result,
        status_code=200,
        media_type="text/event-stream"
    )

# 3. 定义对话请求 (V2 - LangGraph 新版)
@router.post("/api/v2/query", summary="智能体对话接口 (V2 - LangGraph)")
async def query_v2(request_context: ChatMessageRequest) -> StreamingResponse:
    """
    LangGraph 引擎对话接口
    """
    user_id = request_context.context.user_id
    user_query = request_context.query
    logger.info(f"[V2] 用户 {user_id} 发送任务: {user_query}")

    async_generator_result = MultiAgentServiceV2.process_task(request_context, flag=True)

    return StreamingResponse(
        content=async_generator_result,
        status_code=200,
        media_type="text/event-stream"
    )

@router.post("/api/user_sessions")
def get_user_sessions(request: UserSessionsRequest):
    """
    获取用户的所有会话记忆数据。

    Args:
        request: 包含 user_id 的请求体。

    Returns:
        包含用户所有会话信息和记忆的 JSON 响应。
    """
    # 1. 日志记录：记录请求到达
    logger.info("接收到获取用户会话请求")

    # 2. 参数提取：从请求模型中获取目标用户ID
    user_id = request.user_id
    logger.info(f"获取用户 {user_id} 的所有会话记忆数据")

    try:
        # 3. 服务调用 session_service 从底层存储检索所有历史会话
        all_sessions =session_service.get_all_sessions_memory(user_id)
        logger.debug(f"成功获取用户 {user_id} 的 {len(all_sessions)} 个会话")

        # 4. 响应构建：组装并返回标准化的成功 JSON 数据
        return {
            "success": True,
            "user_id": user_id,
            "total_sessions": len(all_sessions),
            "sessions": all_sessions
        }
    except Exception as e:
        # 5. 异常处理：捕获服务层抛出的未知错误，记录日志并返回错误标识
        logger.error(f"获取用户 {user_id} 的会话数据时出错: {str(e)}")
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e)
        }
