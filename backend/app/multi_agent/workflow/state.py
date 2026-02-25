"""
LangGraph 状态定义

- AgentState: 主状态对象（黑板模式）
- RetrievalSubState: 检索子图内部状态
"""

from typing import TypedDict, Annotated, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage
import operator


class RetrievalStrategy(TypedDict):
    """检索策略参数"""
    intent_type: str
    query_tags: List[str]
    search_kwargs: Dict[str, Any]


class DiagnosisStep(TypedDict):
    """诊断步骤"""
    step: str
    result: Optional[str]


class AgentState(TypedDict):
    """核心状态对象 (The Blackboard)"""

    # --- 基础通信 ---
    messages: Annotated[List[BaseMessage], operator.add]

    # --- 上下文信息 ---
    session_id: str
    user_id: str
    trace_id: str

    # --- 业务状态 ---
    current_intent: Optional[str]
    intent_confidence: float
    original_query: Optional[str]

    # --- 槽位管理 ---
    slots: Dict[str, Any]
    missing_slots: List[str]
    ask_user_count: int

    # --- 检索结果 ---
    retrieved_documents: Annotated[List[Any], operator.add]

    # --- 结果控制 ---
    need_human_help: bool
    final_report: Optional[Dict[str, Any]]


class RetrievalSubState(TypedDict):
    """
    检索子图内部状态

    子图在受控范围内自主循环：search → evaluate → rewrite_query → search → ...
    最多循环 max_retries 次，超限强制退出。
    """
    query: str                          # 当前检索 query（可被 rewrite_query 改写）
    original_query: str                 # 原始用户 query（不变）
    intent: str                         # 意图类型
    slots: Dict[str, Any]              # 槽位（local_tools 需要）
    source: str                         # 当前数据源: kb / web / local_tools
    documents: List[Dict[str, Any]]     # 本轮检索结果
    is_sufficient: bool                 # evaluate 判定结果是否足够
    suggestion: str                     # evaluate 建议: pass / retry_same / switch_source
    loop_count: int                     # 当前循环次数
    max_retries: int                    # 最大循环次数（确定性兜底）
