"""
Explain / Audit API: Enterprise-grade transparency
- Exposes full decision trace without recomputation
- Structured JSON output for compliance/audit
- Source all data from existing state/logs
"""
from typing import Dict, Any, Optional, List
from rag.logger import get_logger


def explain_response(result: Dict[str, Any], trace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate explain/audit output from execution result.
    
    Extracts all available information from the result state without recomputation.
    Structured JSON output suitable for compliance/audit purposes.
    
    Args:
        result: Result dictionary from supervisor.invoke()
        trace_id: Optional trace_id for logging
    
    Returns:
        Structured explain/audit output:
        {
            "trace_id": str,
            "original_query": str,
            "decision_path": List[str],
            "intent": str,
            "tools_used": List[str],
            "metadata_filters": Dict[str, Any] | None,
            "documents_used": List[str],
            "claims": List[Dict[str, str]],
            "sources_used": List[str],
            "confidence": float,
            "confidence_reason": str,
            "refusal_reason": str | None,
            "answer": str
        }
    """
    logger = get_logger(trace_id)
    logger.info("Generating explain/audit output", trace_id=result.get("trace_id"))
    
    # Extract all available fields from result
    trace_id_value = result.get("trace_id") or trace_id
    original_query = result.get("question", "")
    decision_path = result.get("decision_path", [])
    intent = result.get("intent", "unknown")
    used_tools = result.get("used_tools", [])
    metadata_filters = result.get("metadata_filters")
    answer = result.get("answer", "")
    claims = result.get("claims", [])
    sources_used = result.get("sources_used", [])
    confidence = result.get("confidence", 0.0)
    confidence_reason = result.get("confidence_reason", "")
    
    # Extract documents_used from research_notes or context
    documents_used = []
    if result.get("research_notes"):
        documents_used = result.get("research_notes", [])
    elif result.get("context"):
        documents_used = result.get("context", [])
    
    # Determine refusal reason (if applicable)
    refusal_reason = None
    if answer and "don't know" in answer.lower():
        if not documents_used or len(documents_used) == 0:
            refusal_reason = "No documents retrieved for query"
        elif metadata_filters:
            refusal_reason = f"Metadata filter matched zero documents: {metadata_filters}"
        else:
            refusal_reason = "Context insufficient to answer query"
    
    # Structure explain output
    explain_output = {
        "trace_id": trace_id_value,
        "original_query": original_query,
        "decision_path": decision_path if isinstance(decision_path, list) else [decision_path] if decision_path else [],
        "intent": intent,
        "tools_used": used_tools,
        "metadata_filters": metadata_filters,
        "documents_used": [doc[:200] + "..." if len(doc) > 200 else doc for doc in documents_used],  # Truncate long docs
        "claims": claims,
        "sources_used": sources_used,
        "confidence": float(confidence) if confidence else 0.0,
        "confidence_reason": confidence_reason,
        "refusal_reason": refusal_reason,
        "answer": answer
    }
    
    logger.info("Explain/audit output generated",
                trace_id=trace_id_value,
                has_claims=len(claims) > 0,
                has_refusal=refusal_reason is not None,
                confidence=confidence)
    
    return explain_output


def explain_from_trace_id(trace_id: str, result_store: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Explain from trace_id (future enhancement: requires result storage).
    
    For now, this is a placeholder that demonstrates the API structure.
    In production, this would query a result store or log aggregation system.
    
    Args:
        trace_id: Trace ID to look up
        result_store: Optional in-memory store (for demo purposes)
    
    Returns:
        Explain output if found, None otherwise
    """
    logger = get_logger(trace_id)
    logger.info("Looking up explain from trace_id", trace_id=trace_id)
    
    if result_store and trace_id in result_store:
        result = result_store[trace_id]
        return explain_response(result, trace_id=trace_id)
    
    # In production, this would query logs/database
    logger.warning("Result not found for trace_id", trace_id=trace_id)
    return None
