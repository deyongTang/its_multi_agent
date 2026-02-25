"""
LangGraph Workflow Graph Definition (v2.0 - Hybrid Architecture)

外层显式管道 + 内层自主循环检索子图
  intent → slot_filling → [检索子图: 自主循环] → verify → generate_report → END
"""

from langgraph.graph import StateGraph, END
from multi_agent.workflow.state import AgentState

# Nodes
from multi_agent.workflow.nodes.intent_node import node_intent
from multi_agent.workflow.nodes.slot_filling_node import node_slot_filling
from multi_agent.workflow.nodes.ask_user_node import node_ask_user
from multi_agent.workflow.nodes.general_chat_node import node_general_chat
from multi_agent.workflow.nodes.merge_verify_nodes import node_verify
from multi_agent.workflow.nodes.action_nodes import node_escalate, node_generate_report

# Retrieval SubGraph
from multi_agent.workflow.retrieval_subgraph import build_retrieval_subgraph

# Edges
from multi_agent.workflow.edges import route_intent, route_slot_check, route_ask_user_result
from multi_agent.workflow.edges.routers_phase2 import route_verify_result

from infrastructure.logging.logger import logger


def _get_last_user_query(state: AgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            return msg.content
    return ""


# 预编译检索子图（避免每次请求重复编译）
_retrieval_subgraph = build_retrieval_subgraph()


async def node_retrieval(state: AgentState) -> dict:
    """
    检索子图包装节点：桥接 AgentState ↔ RetrievalSubState
    将主图状态映射到子图，运行子图，将结果写回主图
    """
    user_query = _get_last_user_query(state)
    intent = state.get("current_intent", "")
    slots = state.get("slots", {})
    # 追问场景：用原始问题 + 用户补充信息合并为检索 query
    original_query = state.get("original_query") or user_query
    combined_query = f"{original_query} {user_query}".strip() if original_query != user_query else user_query
    # 多轮对话：把 slots 中提取到的关键信息（如地点）拼入 query
    slot_context = " ".join(str(v) for v in slots.values() if v)
    if slot_context and slot_context not in combined_query:
        combined_query = f"{combined_query} {slot_context}".strip()

    # 构建子图输入
    sub_input = {
        "query": combined_query,
        "original_query": original_query,
        "intent": intent,
        "slots": slots,
        "source": "",
        "documents": [],
        "is_sufficient": False,
        "suggestion": "",
        "loop_count": 0,
        "max_retries": 3,
    }

    # 运行子图
    result = await _retrieval_subgraph.ainvoke(sub_input)

    # 将子图结果写回主图
    docs = result.get("documents", [])
    logger.info(f"[Retrieval SubGraph] 完成，返回 {len(docs)} 条结果，循环 {result.get('loop_count', 0)} 次")

    return {"retrieved_documents": docs}


def create_workflow_graph():
    """构建 v2.0 混合架构工作流"""
    logger.info("Building LangGraph v2.0 Workflow (Hybrid Architecture)...")

    workflow = StateGraph(AgentState)

    # --- Nodes ---
    workflow.add_node("intent", node_intent)
    workflow.add_node("slot_filling", node_slot_filling)
    workflow.add_node("ask_user", node_ask_user)
    workflow.add_node("general_chat", node_general_chat)
    workflow.add_node("retrieval", node_retrieval)
    workflow.add_node("verify", node_verify)
    workflow.add_node("escalate", node_escalate)
    workflow.add_node("generate_report", node_generate_report)

    # --- Entry ---
    workflow.set_entry_point("intent")

    # --- Edges ---
    workflow.add_conditional_edges("intent", route_intent, {
        "general_chat": "general_chat",
        "slot_filling": "slot_filling",
    })

    workflow.add_conditional_edges("slot_filling", route_slot_check, {
        "ask_user": "ask_user",
        "retrieval": "retrieval",
    })

    workflow.add_edge("retrieval", "verify")

    workflow.add_conditional_edges("verify", route_verify_result, {
        "generate_report": "generate_report",
        "escalate": "escalate",
    })

    # End Nodes
    workflow.add_edge("general_chat", END)
    workflow.add_conditional_edges("ask_user", route_ask_user_result, {
        "escalate": "escalate",
        "end": END,
    })
    workflow.add_edge("generate_report", END)
    workflow.add_edge("escalate", END)

    # --- Compile ---
    app = workflow.compile()

    logger.info("LangGraph v2.0 Compiled Successfully.")
    return app
