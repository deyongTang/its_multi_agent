from langchain_core.messages import ToolMessage
from multi_agent.workflow.state import AgentState, RetrievalStrategy
from infrastructure.logging.logger import logger

def node_strategy_gen(state: AgentState) -> dict:
    """
    Strategy Generation Node
    
    Implements Active Retrieval Protocol:
    1. Analyzes intent & slots
    2. Generates dynamic weights for ES (Keyword vs Vector)
    3. Configures search filters
    """
    intent = state.get("current_intent")
    slots = state.get("slots", {})
    
    logger.info(f"Generating strategy for intent: {intent}, slots: {slots}")
    
    # Default Strategy
    strategy: RetrievalStrategy = {
        "intent_type": intent or "general",
        "keyword_weight": 0.5,
        "vector_weight": 0.5,
        "search_kwargs": {}
    }
    
    # Dynamic Logic (Hardcoded rules as per Design v1.3)
    
    # Case 1: Technical Issue with explicit Error Code
    if intent == "technical_issue" and "error_code" in slots:
        strategy["keyword_weight"] = 0.9
        strategy["vector_weight"] = 0.1
        strategy["search_kwargs"]["filter_type"] = "troubleshooting"
        
    # Case 2: Technical Issue with vague description
    elif intent == "technical_issue" and "error_phenomenon" in slots:
        strategy["keyword_weight"] = 0.3
        strategy["vector_weight"] = 0.7
        
    # Case 3: POI/Service (Lean towards tools)
    elif intent in ["poi_navigation", "service_station"]:
        strategy["keyword_weight"] = 0.8 # Names are specific
        strategy["vector_weight"] = 0.2
        
    return {"retrieval_strategy": strategy}
