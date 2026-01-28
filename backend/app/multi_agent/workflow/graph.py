"""
LangGraph Workflow Graph Definition (v1.3)

Implements the full "Industrial-Grade" orchestration logic:
- Intent Classification
- Slot Filling Loop (with User Interrupt)
- Active Retrieval (Strategy Generation)
- Parallel Execution (ES, Baidu, Tools)
- Result Merge & Verification
- Retry Loop (Query Expansion)
- Human Escalation
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from multi_agent.workflow.state import AgentState

# Import Nodes
from multi_agent.workflow.nodes.intent_node import node_intent
from multi_agent.workflow.nodes.slot_filling_node import node_slot_filling
from multi_agent.workflow.nodes.ask_user_node import node_ask_user
from multi_agent.workflow.nodes.general_chat_node import node_general_chat

# Phase 2 Nodes
from multi_agent.workflow.nodes.strategy_gen_node import node_strategy_gen
from multi_agent.workflow.nodes.search_nodes import node_search_es, node_search_baidu, node_search_tools
from multi_agent.workflow.nodes.merge_verify_nodes import node_merge_rerank, node_verify
from multi_agent.workflow.nodes.action_nodes import node_expand_query, node_escalate, node_generate_report

# Import Edges
from multi_agent.workflow.edges import (
    route_intent,
    route_slot_check,
    route_parallel_execution,
    route_verify_result
)

from infrastructure.logging.logger import logger

def create_workflow_graph():
    """
    Builds the compiled LangGraph application.
    """
    logger.info("Building LangGraph v1.3 Workflow...")
    
    workflow = StateGraph(AgentState)
    
    # --- 1. Add Nodes ---
    # Core Logic
    workflow.add_node("intent", node_intent)
    workflow.add_node("slot_filling", node_slot_filling)
    workflow.add_node("ask_user", node_ask_user)
    workflow.add_node("general_chat", node_general_chat)
    
    # Retrieval & Action Logic
    workflow.add_node("strategy_gen", node_strategy_gen)
    
    # Parallel Search Nodes
    workflow.add_node("search_es", node_search_es)
    workflow.add_node("search_baidu", node_search_baidu)
    workflow.add_node("search_tools", node_search_tools)
    
    # Merge & Verify
    workflow.add_node("merge_rerank", node_merge_rerank)
    workflow.add_node("verify", node_verify)
    
    # Post-Process
    workflow.add_node("expand_query", node_expand_query)
    workflow.add_node("escalate", node_escalate)
    workflow.add_node("generate_report", node_generate_report)
    
    # --- 2. Set Entry Point ---
    workflow.set_entry_point("intent")
    
    # --- 3. Define Edges & Routing ---
    
    # Intent Router
    workflow.add_conditional_edges(
        "intent",
        route_intent,
        {
            "general_chat": "general_chat",
            "slot_filling": "slot_filling",  # Tech/POI/Service go here
        }
    )
    
    # Slot Filling Loop
    workflow.add_conditional_edges(
        "slot_filling",
        route_slot_check,
        {
            "ask_user": "ask_user",         # Loop back for more info
            "strategy_gen": "strategy_gen"  # Proceed if slots full
        }
    )
    
    # Strategy -> Parallel Execution (Fan-Out)
    workflow.add_conditional_edges(
        "strategy_gen",
        route_parallel_execution,
        # The router returns a list of node names to execute
        ["search_es", "search_baidu", "search_tools"] 
    )
    
    # Fan-In (All search nodes go to Merge)
    workflow.add_edge("search_es", "merge_rerank")
    workflow.add_edge("search_baidu", "merge_rerank")
    workflow.add_edge("search_tools", "merge_rerank")
    
    # Merge -> Verify
    workflow.add_edge("merge_rerank", "verify")
    
    # Verification Router (Retry Logic)
    workflow.add_conditional_edges(
        "verify",
        route_verify_result,
        {
            "generate_report": "generate_report",
            "expand_query": "expand_query",
            "escalate": "escalate"
        }
    )
    
    # Retry Loop
    workflow.add_edge("expand_query", "strategy_gen")
    
    # End Nodes
    workflow.add_edge("general_chat", END)
    workflow.add_edge("ask_user", END) # Interrupt point
    workflow.add_edge("generate_report", END)
    workflow.add_edge("escalate", END)
    
    # --- 4. Compile ---
    checkpointer = MemorySaver()
    
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["ask_user"]
    )
    
    logger.info("LangGraph v1.3 Compiled Successfully.")
    return app