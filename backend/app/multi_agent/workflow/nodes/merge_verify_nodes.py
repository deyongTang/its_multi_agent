from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger

def node_merge_rerank(state: AgentState) -> dict:
    """
    Merge & Rerank Node (Fan-In)
    
    1. Aggregates results from all parallel search nodes.
    2. Dedupes.
    3. (Optional) Applies RRF or LLM Reranking.
    """
    # Note: In LangGraph, parallel nodes might return a list of dicts update
    # But here we assume the state 'retrieved_documents' is being appended to 
    # or we handle the reducer logic. 
    # For simplicity in this skeleton, we assume 'retrieved_documents' holds all raw results.
    
    raw_docs = state.get("retrieved_documents", [])
    logger.info(f"Merging {len(raw_docs)} documents...")
    
    # Simple Dedupe by content
    unique_docs = []
    seen = set()
    for doc in raw_docs:
        # Assuming doc is dict-like
        content = doc.get("content", "")
        if content not in seen:
            seen.add(content)
            unique_docs.append(doc)
            
    # TODO: Implement RRF here
    
    return {"retrieved_documents": unique_docs}

def node_verify(state: AgentState) -> dict:
    """
    Verification Node
    
    Checks if the results are sufficient to answer the user's query.
    """
    docs = state.get("retrieved_documents", [])
    logger.info(f"Verifying {len(docs)} documents...")
    
    # Simple Logic: If we have docs, we are good.
    # Future: Use LLM to judge "Is this helpful?"
    
    # This node doesn't update state much, just passes through 
    # for the conditional edge 'route_verify_result' to check.
    return {}
