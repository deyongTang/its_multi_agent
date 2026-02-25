"""
检索子图构建器 (Retrieval SubGraph Builder)

构建带自主循环的检索子图，嵌入主图替代原有的 strategy_gen + search + route_kb_check
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from multi_agent.workflow.state import RetrievalSubState
from multi_agent.workflow.nodes.retrieval_subgraph_nodes import (
    node_retrieval_dispatch,
    node_retrieval_search,
    node_retrieval_evaluate,
    node_retrieval_rewrite,
)
from infrastructure.logging.logger import logger


def route_evaluate(state: RetrievalSubState) -> Literal["exit", "rewrite"]:
    """evaluate 后的路由：通过则退出，否则改写重试"""
    if state.get("is_sufficient"):
        return "exit"
    if state.get("loop_count", 0) >= state.get("max_retries", 3):
        logger.warning(f"[Retrieval] 达到最大重试次数 {state.get('max_retries', 3)}，强制退出")
        return "exit"
    return "rewrite"


def build_retrieval_subgraph() -> StateGraph:
    """构建检索子图"""
    sg = StateGraph(RetrievalSubState)

    sg.add_node("dispatch", node_retrieval_dispatch)
    sg.add_node("search", node_retrieval_search)
    sg.add_node("evaluate", node_retrieval_evaluate)
    sg.add_node("rewrite", node_retrieval_rewrite)

    sg.set_entry_point("dispatch")
    sg.add_edge("dispatch", "search")
    sg.add_edge("search", "evaluate")
    sg.add_conditional_edges("evaluate", route_evaluate, {"exit": END, "rewrite": "rewrite"})
    sg.add_edge("rewrite", "search")

    return sg.compile()
