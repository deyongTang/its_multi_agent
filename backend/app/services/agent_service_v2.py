from collections.abc import AsyncGenerator
from multi_agent.workflow.runner import WorkflowRunner
from services.workflow_stream_service import process_workflow_stream
from schemas.request import ChatMessageRequest
from services.session_service import session_service
from utils.response_util import ResponseFactory
from infrastructure.logging.logger import logger, trace_id_var
import traceback
import re
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

            # 1. 准备历史对话（包含当前输入，已裁剪到最近 3 轮）
            # prepare_history 会自动追加当前 user_query
            chat_history = session_service.prepare_history(user_id, session_id, user_query)

            # 2. 分离历史对话和当前输入
            # chat_history 最后一条是当前输入，需要分离出来避免重复
            history_without_current = chat_history[:-1] if len(chat_history) > 1 else []

            logger.info(f"[{request_id}] 传入历史消息数: {len(history_without_current)}")

            # 3. 运行 LangGraph 工作流（传入历史对话）
            workflow_stream = workflow_runner.stream_run(
                user_query=user_query,
                user_id=user_id,
                session_id=session_id,
                chat_history=history_without_current  # ✅ 传入历史对话
            )

            # 3. 处理流式响应并累积最终结果
            full_ai_response = ""
            is_ask_user_response = False
            pending_intent = ""

            async for chunk in process_workflow_stream(workflow_stream):
                yield chunk
                try:
                    if chunk.startswith("data:"):
                        import json
                        data = json.loads(chunk[5:].strip())
                        kind = data.get("content", {}).get("kind")
                        text = data.get("content", {}).get("text")
                        if kind == ContentKind.ANSWER and text:
                            full_ai_response += text
                            if data.get("is_ask_user"):
                                is_ask_user_response = True
                                pending_intent = data.get("pending_intent", "")
                except:
                    pass

            logger.info(f"[{request_id}] LangGraph 任务处理完成")

            # 4. 持久化历史对话
            if full_ai_response:
                format_result = re.sub(r'\n+', '\n', full_ai_response)
                msg = {"role": "assistant", "content": format_result}
                if is_ask_user_response:
                    msg["is_ask_user"] = True
                    if pending_intent:
                        msg["pending_intent"] = pending_intent
                chat_history.append(msg)
                session_service.save_history(user_id, session_id, chat_history)
                logger.info(f"[{request_id}] 会话历史已保存到数据库")

        except Exception as e:
            logger.error(f"AgentServiceV2.process_task 执行出错: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            
            text = f"❌ 系统错误 (V2): {str(e)}"
            yield "data: " + ResponseFactory.build_text(
                text, ContentKind.PROCESS
            ).model_dump_json() + "\n\n"