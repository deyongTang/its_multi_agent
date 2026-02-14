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
            
            async for chunk in process_workflow_stream(workflow_stream):
                # 实时推送给前端
                yield chunk
                
                # 尝试从 SSE 格式中提取 ANSWER 内容进行拼接
                # chunk 格式: "data: {...}\n\n"
                try:
                    if chunk.startswith("data:"):
                        import json
                        json_str = chunk[5:].strip()
                        data = json.loads(json_str)
                        # 检查新旧字段结构 (kind 或 type)
                        kind = data.get("content", {}).get("kind") or data.get("type")
                        text = data.get("content", {}).get("text") or data.get("content")
                        
                        if kind == ContentKind.ANSWER and text:
                            full_ai_response += text
                except:
                    pass

            logger.info(f"[{request_id}] LangGraph 任务处理完成")

            # 4. 持久化历史对话到 MySQL
            # 只有当 AI 有实际回答时才保存
            if full_ai_response:
                # 格式化处理 (去除多余换行)
                format_result = re.sub(r'\n+', '\n', full_ai_response)
                
                # 追加 AI 回复
                chat_history.append({"role": "assistant", "content": format_result})
                
                # 写入数据库
                session_service.save_history(user_id, session_id, chat_history)
                logger.info(f"[{request_id}] 会话历史已保存到数据库")

        except Exception as e:
            logger.error(f"AgentServiceV2.process_task 执行出错: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            
            text = f"❌ 系统错误 (V2): {str(e)}"
            yield "data: " + ResponseFactory.build_text(
                text, ContentKind.PROCESS
            ).model_dump_json() + "\n\n"