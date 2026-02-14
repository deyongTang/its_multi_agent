"""
LangGraph 状态定义

定义工作流的核心状态结构，包括：
- AgentState: 主状态对象（黑板模式）
- RetrievalStrategy: 检索策略配置
- DiagnosisStep: 诊断步骤记录
"""

from typing import TypedDict, Annotated, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage
import operator


class RetrievalStrategy(TypedDict):
    """
    检索策略配置 (业务层)
    
    仅定义业务维度的检索需求，不包含底层实现细节（如 ES/Vector 权重）。
    """
    intent_type: str                    # 意图类型 (tech/poi/service/chitchat)
    query_tags: List[str]               # 业务标签 (e.g. ['BlueScreen', 'Lenovo'])
    search_kwargs: Dict[str, Any]       # 其他业务参数 (e.g. limit, time_range)


class DiagnosisStep(TypedDict):
    """诊断步骤记录"""

    step_index: int  # 步骤序号
    action: str  # 执行的动作
    observation: str  # 观察结果
    status: str  # 状态 (success/failed/pending)


class AgentState(TypedDict):
    """
    核心状态对象 (The Blackboard)

    所有节点共享此状态，通过更新状态字段来传递信息
    """

    # --- 基础通信 (支持多轮对话) ---
    # Annotated[..., operator.add] 确保消息是追加而非覆盖
    messages: Annotated[List[BaseMessage], operator.add]

    # --- 上下文信息 ---
    session_id: str  # 会话ID
    user_id: str  # 用户ID
    trace_id: str  # 追踪ID（与现有 trace_id_var 集成）

    # --- 业务状态 ---
    current_intent: Optional[str]  # 当前意图 (tech/poi/service/chitchat)
    intent_confidence: float  # 意图置信度

    # --- 槽位管理 (Context Retention) ---
    # 这里的 slots 会在多轮对话中持久化
    slots: Dict[str, Any]  # 已填充的槽位
    missing_slots: List[str]  # 缺失的槽位
    ask_user_count: int  # 追问次数（防止死循环）

    # --- 检索与执行 ---
    retrieval_strategy: Optional[RetrievalStrategy]  # 检索策略
    retrieved_documents: Annotated[List[Any], operator.add]  # 检索到的文档
    steps: List[DiagnosisStep]  # 执行步骤记录

    # --- 错误处理 ---
    error_log: List[str]  # 错误日志
    retry_count: int  # 重试次数

    # --- 结果控制 ---
    need_human_help: bool  # 是否需要人工介入
    final_report: Optional[Dict[str, Any]]  # 最终报告
