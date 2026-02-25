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

        logger.info(f"开始运行工作流")

        # 2. 构建初始状态
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
            "retrieved_documents": [],
            "need_human_help": False,
            "final_report": None,
        }

        # 3. 运行工作流
        try:
            final_state = await self.graph.ainvoke(initial_state)
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
        config = {}

        # 转换历史对话为 LangChain 格式
        messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=user_query))
        logger.info(f"传入历史消息数: {len(messages)}")

        # 从历史推断追问状态：若历史最后一条 assistant 消息带有 is_ask_user 标记，说明上一轮在追问
        is_followup = bool(chat_history and chat_history[-1].get("is_ask_user"))
        inferred_ask_count = 1 if is_followup else 0
        restored_intent = chat_history[-1].get("pending_intent") if is_followup else None
        # 追问时找到原始问题（ask_user 之前的那条 user 消息）
        original_query = None
        if is_followup:
            for msg in reversed(chat_history[:-1]):  # 跳过 ask_user assistant 消息
                if msg.get("role") == "user":
                    original_query = msg.get("content")
                    break
        logger.info(f"追问状态推断: is_followup={is_followup}, intent={restored_intent}, original_query={original_query!r}")

        # 构建初始状态（每次新请求都从 intent 节点重新开始）
        initial_state: AgentState = {
            "messages": messages,
            "session_id": session_id,
            "user_id": user_id,
            "trace_id": trace_id,
            "current_intent": restored_intent,
            "intent_confidence": 0.0,
            "original_query": original_query,
            "slots": {},
            "missing_slots": [],
            "ask_user_count": inferred_ask_count,
            "retrieved_documents": [],
            "need_human_help": False,
            "final_report": None,
        }

        async for event in self.graph.astream_events(initial_state, config, version="v2"):
            yield event
