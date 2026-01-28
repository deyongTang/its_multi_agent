from typing import Literal, List
from multi_agent.workflow.state import AgentState

def route_parallel_execution(state: AgentState) -> List[str]:
    """
    Parallel Execution Router (Fan-Out)
    
    Determines which search nodes to execute in parallel based on the strategy.
    Returns a list of node names.
    """
    strategy = state.get("retrieval_strategy")
    if not strategy:
        # Fallback if no strategy (shouldn't happen in normal flow)
        return ["search_tools"]
        
    targets = []
    
    # Check weights to decide sources
    # In v1.3 design, we fan-out to all relevant sources defined in the strategy
    # For now, we default to activating all available search nodes 
    # and let them filter internally based on the strategy if needed,
    # or we can explicitly check strategy contents here.
    
    # Active Retrieval Protocol Logic:
    # If explicit error code -> lean towards KB (ES)
    # If vague -> lean towards Vector (ES) + Web (Baidu)
    # If POI/Service -> lean towards Tools
    
    # For robust implementation, we trigger all configured searchers
    # The Merge Node will handle filtering empty results.
    targets.append("search_es")
    targets.append("search_baidu") 
    targets.append("search_tools")
    
    return targets

def route_verify_result(state: AgentState) -> Literal["generate_report", "expand_query", "escalate"]:
    """
    Verification Router
    
    Decides whether to:
    1. Generate final report (Success)
    2. Expand query and retry (Partial/No result & Retry < Limit)
    3. Escalate to human (No result & Retry >= Limit)
    """
    retry_count = state.get("retry_count", 0)
    docs = state.get("retrieved_documents", [])
    
    # Thresholds (can be moved to config)
    MAX_RETRIES = 3
    
    # Simple check: do we have any documents?
    # In future, add 'confidence_score' check from the Verify Node
    has_results = len(docs) > 0
    
    if has_results:
        return "generate_report"
    
    if retry_count >= MAX_RETRIES:
        return "escalate"
    
    return "expand_query"
