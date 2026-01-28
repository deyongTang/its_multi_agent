from collections.abc import AsyncGenerator
from multi_agent.workflow.runner import WorkflowRunner
from services.workflow_stream_service import process_workflow_stream
from schemas.request import ChatMessageRequest
from utils.response_util import ResponseFactory
from infrastructure.logging.logger import logger, trace_id_var
import traceback
from schemas.response import ContentKind

# 初始化全局 WorkflowRunner
workflow_runner = WorkflowRunner()

class MultiAgentServiceV2:
    """
    多智能体业务服务类 V2 (基于 LangGraph)
    """

    @classmethod
    async def process_task(cls, request: ChatMessageRequest, flag: bool) -> AsyncGenerator:
        """
        多智能体处理任务入口（LangGraph 编排引擎）
        Args:
            request:  请求上下文
            flag: 是否允许重试
        Returns:
            AsyncGenerator：异步生成器对象
        """
        request_id = trace_id_var.get()

        try:
            user_id = request.context.user_id
            session_id = request.context.session_id
            user_query = request.query

            logger.info(f"[{request_id}] 用户 {user_id} 发送任务 (LangGraph V2): {user_query}")

            # 运行 LangGraph 工作流
            workflow_stream = workflow_runner.stream_run(
                user_query=user_query,
                user_id=user_id,
                session_id=session_id
            )

            # 处理并转发流式响应
            async for chunk in process_workflow_stream(workflow_stream):
                yield chunk

            logger.info(f"[{request_id}] LangGraph 任务处理完成")

        except Exception as e:
            logger.error(f"AgentServiceV2.process_task 执行出错: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            
            text = f"❌ 系统错误 (V2): {str(e)}"
            yield "data: " + ResponseFactory.build_text(
                text, ContentKind.PROCESS
            ).model_dump_json() + "\n\n"
