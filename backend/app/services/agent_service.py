import re
from collections.abc import AsyncGenerator
from agents.run import Runner
from multi_agent.orchestrator_agent import orchestrator_agent
from schemas.request import ChatMessageRequest
from services.session_service import session_service
from services.stream_response_service import process_stream_response
from utils.response_util import ResponseFactory
from infrastructure.logging.logger import logger, trace_id_var
from schemas.response import ContentKind
import traceback


@DeprecationWarning
class MultiAgentService:
    """
    多智能体业务服务类 (V1: 基于 Orchestrator Agent)
    """

    @classmethod
    async def process_task(cls, request: ChatMessageRequest, flag: bool) -> AsyncGenerator:
        """
        多智能体处理任务入口
        Args:
            request:  请求上下文

        Returns:
            AsyncGenerator：异步生成器对象（必须）
        """
        # 从上下文变量中获取 traceId（由中间件自动设置）
        request_id = trace_id_var.get()

        try:
            # 1. 获取请求上下文的信息
            user_id = request.context.user_id
            session_id = request.context.session_id
            user_query = request.query

            # 2. 准备历史对话
            chat_history = session_service.prepare_history(user_id, session_id, user_query)

            # 记录日志（traceId 会自动添加）
            logger.info(f"用户 {user_id} 发送的待处理任务: {user_query}")

            # 3. 使用 LangSmith 追踪上下文包装执行
            import os
            run_tree = None
            if os.getenv("LANGCHAIN_TRACING_V2") == "true":
                try:
                    from langsmith import Client
                    from langsmith.run_trees import RunTree

                    # 创建 LangSmith 客户端
                    ls_client = Client()

                    # 创建根追踪节点，使用 request_id 作为名称
                    run_tree = RunTree(
                        name=f"MultiAgent-Query-{request_id}",
                        run_type="chain",
                        inputs={
                            "user_id": user_id,
                            "session_id": session_id,
                            "query": user_query
                        },
                        extra={
                            "request_id": request_id,
                            "user_id": user_id,
                            "session_id": session_id
                        },
                        tags=[f"user:{user_id}", f"session:{session_id}", f"req:{request_id}"],
                        client=ls_client
                    )

                    # 开始追踪
                    run_tree.post()

                    # 记录 LangSmith traceId 到日志
                    langsmith_trace_id = run_tree.id
                    logger.info(f"LangSmith traceId: {langsmith_trace_id}")

                except Exception as e:
                    logger.debug(f"创建 LangSmith 追踪失败: {e}")
                    run_tree = None

            # 4. 运行Agent
            streaming_result = Runner.run_streamed(
                starting_agent=orchestrator_agent,
                input=chat_history,  # 列表
                context=user_query,  # 问题
                max_turns=5,  # COT(思考 行动 观察)--->迭代多少次（不是异常重试）
            )

            # 5. 处理Agent的事件流（事件流）
            async for chunk in process_stream_response(streaming_result):
                yield chunk

            # 6. 获取Agent的结果
            agent_result = streaming_result.final_output

            format_agent_result = re.sub(r'\n+', '\n', agent_result)

            # 7. 存储历史对话
            chat_history.append({"role": "assistant", "content": format_agent_result})

            session_service.save_history(user_id, session_id, chat_history)

            logger.info(f"任务处理完成")

            # 8. 结束 LangSmith 追踪
            if run_tree:
                try:
                    run_tree.end(outputs={"result": format_agent_result[:500]})
                    run_tree.patch()
                except Exception as e:
                    logger.debug(f"结束 LangSmith 追踪失败: {e}")

        except Exception as e:
            # 记录错误日志（traceId 会自动添加）
            logger.error(f"AgentService.process_query执行出错: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")

            # 标记追踪失败
            if run_tree:
                try:
                    run_tree.end(error=str(e))
                    run_tree.patch()
                except:
                    pass

            text = f"❌ 系统错误: {str(e)}"
            yield "data: " + ResponseFactory.build_text(
                text, ContentKind.PROCESS
            ).model_dump_json() + "\n\n"

            # 如果允许重试，则启动重试流程
            if flag:
                text = f"🔄 正在尝试自动重试..."
                yield "data: " + ResponseFactory.build_text(
                    text, ContentKind.PROCESS
                ).model_dump_json() + "\n\n"

                # 递归调用进行重试
                async for item in MultiAgentService.process_task(request,flag=False):
                    yield item