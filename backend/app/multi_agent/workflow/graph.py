"""
LangGraph Workflow Graph Definition (v1.4 - Explicit Sequential Pipeline)

Implements the explicit fallback logic:
- Intent -> Strategy -> Dispatch
- Dispatch (Tech) -> KB -> Check KB -> (if miss) -> Web
- Dispatch (Info) -> Web
- Dispatch (Map) -> Tools
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from multi_agent.workflow.state import AgentState

# Redis Checkpointer 支持
try:
    from langgraph.checkpoint.redis import RedisSaver
    from infrastructure.redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Import Nodes
from multi_agent.workflow.nodes.intent_node import node_intent
from multi_agent.workflow.nodes.slot_filling_node import node_slot_filling
from multi_agent.workflow.nodes.ask_user_node import node_ask_user
from multi_agent.workflow.nodes.general_chat_node import node_general_chat

# Phase 2 Nodes
from multi_agent.workflow.nodes.strategy_gen_node import node_strategy_gen
from multi_agent.workflow.nodes.search_nodes import node_query_knowledge, node_search_web, node_query_local_tools
from multi_agent.workflow.nodes.merge_verify_nodes import node_merge_results, node_verify
from multi_agent.workflow.nodes.action_nodes import node_expand_query, node_escalate, node_generate_report

# Import Edges
from multi_agent.workflow.edges import (
    route_intent,
    route_slot_check,
)
# 新的显式路由器
from multi_agent.workflow.edges.routers_phase2 import (
    route_dispatch,
    route_kb_check,
    route_verify_result
)

from infrastructure.logging.logger import logger

def create_workflow_graph():
    """
    Builds the compiled LangGraph application.
    """
    logger.info("Building LangGraph v1.4 Workflow (Explicit Pipeline)...")
    
    workflow = StateGraph(AgentState)
    
    # --- 1. Add Nodes ---
    workflow.add_node("intent", node_intent)
    workflow.add_node("slot_filling", node_slot_filling)
    workflow.add_node("ask_user", node_ask_user)
    workflow.add_node("general_chat", node_general_chat)
    
    workflow.add_node("strategy_gen", node_strategy_gen)
    
    workflow.add_node("query_knowledge", node_query_knowledge)
    workflow.add_node("search_web", node_search_web)
    workflow.add_node("query_local_tools", node_query_local_tools)
    
    workflow.add_node("merge_results", node_merge_results)
    workflow.add_node("verify", node_verify)
    
    workflow.add_node("expand_query", node_expand_query)
    workflow.add_node("escalate", node_escalate)
    workflow.add_node("generate_report", node_generate_report)
    
    # --- 2. Set Entry Point ---
    workflow.set_entry_point("intent")
    
    # --- 3. Define Edges & Routing ---
    
    # Intent Processing
    workflow.add_conditional_edges(
        "intent",
        route_intent,
        {
            "general_chat": "general_chat",
            "slot_filling": "slot_filling",
        }
    )
    
    # Slot Filling Loop
    workflow.add_conditional_edges(
        "slot_filling",
        route_slot_check,
        {
            "ask_user": "ask_user",
            "strategy_gen": "strategy_gen"
        }
    )
    
    # --- Explicit Dispatching (No more parallel fan-out) ---
    workflow.add_conditional_edges(
        "strategy_gen",
        route_dispatch,
        {
            "query_knowledge": "query_knowledge",
            "search_web": "search_web",
            "query_local_tools": "query_local_tools"
        }
    )
    
    # --- Sequential Fallback Logic ---
    
    # 1. Knowledge Base Path: KB -> Check -> (Web OR Merge)
    workflow.add_conditional_edges(
        "query_knowledge",
        route_kb_check,
        {
            "merge_results": "merge_results",
            "search_web": "search_web"  # 显式指向 Web 兜底
        }
    )
    
    # 2. Web Search Path: Web -> Merge
    workflow.add_edge("search_web", "merge_results")
    
    # 3. Tools Path: Tools -> Merge
    workflow.add_edge("query_local_tools", "merge_results")
    
    # --- Verification & Reporting ---
    
    workflow.add_edge("merge_results", "verify")
    
    workflow.add_conditional_edges(
        "verify",
        route_verify_result,
        {
            "generate_report": "generate_report",
            "escalate": "escalate"
        }
    )
    
    # End Nodes
    workflow.add_edge("general_chat", END)
    workflow.add_edge("ask_user", END)
    workflow.add_edge("generate_report", END)
    workflow.add_edge("escalate", END)
    
    # --- 4. Compile ---
    if REDIS_AVAILABLE:
        checkpointer = RedisSaver(redis_client) if REDIS_AVAILABLE else MemorySaver()
    else:
        checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)

    logger.info("LangGraph v1.4 Compiled Successfully.")
    return app