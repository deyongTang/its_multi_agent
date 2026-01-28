"""
LangGraph 工作流运行器

提供工作流的执行接口，集成 LangSmith 追踪
"""

from typing import Dict, Any, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
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

        # 2. 如果没有 thread_id，生成新的
        if not thread_id:
            thread_id = f"thread_{session_id}_{uuid.uuid4().hex[:8]}"

        logger.info(f"[{trace_id}] 开始运行工作流，thread_id: {thread_id}")

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

        # 5. 运行工作流
        try:
            final_state = await self.graph.ainvoke(initial_state, config)
            logger.info(f"[{trace_id}] 工作流运行完成")
            return final_state

        except Exception as e:
            logger.error(f"[{trace_id}] 工作流运行异常: {e}")
            raise

    async def stream_run(
        self,
        user_query: str,
        user_id: str,
        session_id: str,
        thread_id: str = None,
    ) -> AsyncGenerator:
        """
        以流式方式运行工作流

        Args:
            user_query: 用户查询
            user_id: 用户ID
            session_id: 会话ID
            thread_id: 线程ID

        Yields:
            LangGraph 事件流
        """
        trace_id = trace_id_var.get()
        if not thread_id:
            thread_id = f"thread_{session_id}_{uuid.uuid4().hex[:8]}"

        logger.info(f"[{trace_id}] 开始流式运行工作流，thread_id: {thread_id}")

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

        config = {"configurable": {"thread_id": thread_id}}

        # 使用 astream_events (v2) 获取细粒度事件
        async for event in self.graph.astream_events(initial_state, config, version="v2"):
            yield event
