"""
LangGraph 工作流运行器

提供工作流的执行接口
LangSmith 追踪会自动启用（如果环境变量已配置）
"""

from typing import Dict, Any, AsyncGenerator, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from multi_agent.workflow.graph import create_workflow_graph
from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger, trace_id_var
import uuid


class WorkflowRunner:
    """LangGraph 工作流运行器"""

    def __init__(self):
        """初始化运行器"""
        self.graph = create_workflow_graph()
        logger.info("WorkflowRunner 初始化完成")

    async def run(
        self,
        user_query: str,
        user_id: str,
        session_id: str,
        thread_id: str = None,
    ) -> Dict[str, Any]:
        """
        运行工作流（非流式）

        Args:
            user_query: 用户查询
            user_id: 用户ID
            session_id: 会话ID
            thread_id: 线程ID（用于恢复会话）

        Returns:
            最终状态
        """
        # 1. 从上下文变量获取 trace_id
        trace_id = trace_id_var.get()

        # 2. 如果没有 thread_id，生成确定性的 ID (绑定 session_id)
        if not thread_id:
            # 【关键修正】企业级实践：thread_id 必须是确定性的，不能使用 uuid
            thread_id = f"thread_{user_id}_{session_id}"

        logger.info(f"开始运行工作流，thread_id: {thread_id}")

        # 3. 构建初始状态
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_query)],
            "session_id": session_id,
            "user_id": user_id,
            "trace_id": trace_id,
            "current_intent": None,
            "intent_confidence": 0.0,
            "slots": {},
            "missing_slots": [],
            "ask_user_count": 0,
            "retrieval_strategy": None,
            "retrieved_documents": [],
            "steps": [],
            "error_log": [],
            "retry_count": 0,
            "need_human_help": False,
            "final_report": None,
        }

        # 4. 配置运行参数（包含 thread_id 用于持久化）
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # 5. 运行工作流（LangSmith 会自动追踪）
        try:
            final_state = await self.graph.ainvoke(initial_state, config)
            logger.info("工作流运行完成")
            return final_state

        except Exception as e:
            logger.error(f"工作流运行异常: {e}")
            raise

    async def stream_run(
        self,
        user_query: str,
        user_id: str,
        session_id: str,
        chat_history: List[Dict[str, Any]] | None = None,
        thread_id: str | None = None,
    ) -> AsyncGenerator:
        """
        以流式方式运行工作流（支持历史对话和 Checkpointer）

        Args:
            user_query: 用户查询
            user_id: 用户ID
            session_id: 会话ID
            chat_history: 历史对话（OpenAI 格式）
            thread_id: 线程ID

        Yields:
            LangGraph 事件流
        """
        trace_id = trace_id_var.get()
        if not thread_id:
            thread_id = f"thread_{user_id}_{session_id}"

        config = {"configurable": {"thread_id": thread_id}}

        # 1. 检查是否有 Checkpointer 保存的状态
        try:
            existing_state = self.graph.get_state(config)
            has_checkpoint = existing_state and existing_state.values
        except Exception as e:
            logger.warning(f"获取 Checkpointer 状态失败: {e}")
            has_checkpoint = False

        if has_checkpoint:
            # 2. 有 Checkpoint：追加新消息，继续执行
            logger.info(f"从 Checkpointer 恢复状态，thread_id: {thread_id}")
            self.graph.update_state(
                config,
                {"messages": [HumanMessage(content=user_query)]}
            )
            # 继续执行（不传 initial_state）
            async for event in self.graph.astream_events(None, config, version="v2"):
                yield event
        else:
            # 3. 没有 Checkpoint：初始化状态
            logger.info(f"初始化新工作流，thread_id: {thread_id}")

            # 4. 转换历史对话为 LangChain 格式
            messages = []
            if chat_history:
                for msg in chat_history:
                    role = msg.get("role")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))
                    # system 消息暂时忽略（可以在 Prompt 中处理）

            # 5. 追加当前用户输入
            messages.append(HumanMessage(content=user_query))

            logger.info(f"传入历史消息数: {len(messages)}")

            # 6. 构建初始状态
            initial_state: AgentState = {
                "messages": messages,  # ✅ 包含完整历史
                "session_id": session_id,
                "user_id": user_id,
                "trace_id": trace_id,
                "current_intent": None,
                "intent_confidence": 0.0,
                "slots": {},
                "missing_slots": [],
                "ask_user_count": 0,
                "retrieval_strategy": None,
                "retrieved_documents": [],
                "steps": [],
                "error_log": [],
                "retry_count": 0,
                "need_human_help": False,
                "final_report": None,
            }

            # 7. 运行工作流
            async for event in self.graph.astream_events(initial_state, config, version="v2"):
                yield event
