"""
UI-optimized answer generation with streaming and metadata
Returns answer + metadata for rich UI display
"""
from rag.logger import get_logger
from rag.engine import run_enterprise_query
import uuid

def generate_answer_with_metadata(question: str, trace_id: str = None):
    """
    Generate answer with full metadata for UI display.
    
    Returns:
        dict with:
        - answer: str
        - research_notes: list[str]
        - tool_calls: list[dict]
        - citations: list[str]  # Extracted [Doc N] citations
        - decision_path: str  # "rag" | "web_search" | "roll_dice"
    """
    trace_id = trace_id or str(uuid.uuid4())
    logger = get_logger(trace_id)
    result = run_enterprise_query(question)
    
    # Extract citations from answer
    import re
    citations = re.findall(r'\[Doc \d+\]', result.get("answer", ""))
    citations = list(set(citations))  # Unique citations
    
    # Determine decision path
    decision_path = result.get("decision_path", "rag")
    
    metadata = {
        "answer": result.get("answer", ""),
        "documents": result.get("documents", []),
        "claims": result.get("claims", []),
        "sources_used": result.get("sources_used", []),
        "confidence": result.get("confidence", 0.0),
        "confidence_reason": result.get("confidence_reason", ""),
        "citations": citations,
        "decision_path": decision_path,
        "trace_id": result.get("trace_id", trace_id),
        "intent": result.get("intent", "unknown"),
        "refusal_reason": result.get("refusal_reason")
    }
    
    return metadata

def generate_answer_stream_ui(question: str, trace_id: str = None):
    """
    Generate streaming answer with metadata lookup.
    
    First gets metadata, then streams answer tokens.
    
    Yields:
        dict with:
        - type: "metadata" | "status" | "token" | "done"
        - data: metadata dict, status str, token str, or final data
    """
    trace_id = trace_id or str(uuid.uuid4())

    # Status: running canonical engine
    yield {"type": "status", "data": "🔍 Retrieving evidence"}
    result = run_enterprise_query(question)

    # Yield metadata first (for audit panels)
    yield {
        "type": "metadata",
        "data": {
            "documents": result.get("documents", []),
            "claims": result.get("claims", []),
            "sources_used": result.get("sources_used", []),
            "confidence": result.get("confidence", 0.0),
            "confidence_reason": result.get("confidence_reason", ""),
            "decision_path": result.get("decision_path", "rag"),
            "trace_id": result.get("trace_id", trace_id),
            "intent": result.get("intent", "unknown"),
            "refusal_reason": result.get("refusal_reason"),
        },
    }

    # Status: generating (we already have final text; stream it for UX)
    yield {"type": "status", "data": "✍️ Generating answer"}
    full_answer = result.get("answer", "") or ""
    for ch in full_answer:
        yield {"type": "token", "data": ch}

    import re
    final_citations = re.findall(r'\[Doc \d+\]', full_answer)
    final_citations = list(set(final_citations))

    yield {"type": "done", "data": {"answer": full_answer, "citations": final_citations}}
