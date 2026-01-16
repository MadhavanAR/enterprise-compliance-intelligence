"""
UI-optimized answer generation with streaming and metadata
Returns answer + metadata for rich UI display
"""
from rag.generate_stream import generate_answer_stream
from rag.supervisor import build_supervisor
from rag.logger import get_logger
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
    
    app = build_supervisor()
    
    # Invoke with trace_id in state
    state = {"question": question, "trace_id": trace_id}
    result = app.invoke(state)
    
    # Extract citations from answer
    import re
    citations = re.findall(r'\[Doc \d+\]', result.get("answer", ""))
    citations = list(set(citations))  # Unique citations
    
    # Determine decision path
    decision_path = "rag"
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        decision_path = tool_calls[0].get("tool", "rag")
    
    metadata = {
        "answer": result.get("answer", ""),
        "research_notes": result.get("research_notes", []),
        "tool_calls": tool_calls,
        "citations": citations,
        "decision_path": decision_path,
        "trace_id": trace_id
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
    
    # Step 1: Research (get context)
    from rag.research_team import build_research_graph
    
    research_app = build_research_graph()
    
    # Yield status: retrieving
    yield {
        "type": "status",
        "data": "🔍 Retrieving documents"
    }
    
    # Research (get context)
    research_result = research_app.invoke({"question": question, "trace_id": trace_id})
    
    # Extract metadata
    tool_calls = research_result.get("tool_calls", [])
    decision_path = "rag"
    if tool_calls:
        decision_path = tool_calls[0].get("tool", "rag")
    
    research_notes = research_result.get("research_notes", [])
    
    # Yield metadata
    yield {
        "type": "metadata",
        "data": {
            "research_notes": research_notes,
            "tool_calls": tool_calls,
            "decision_path": decision_path,
            "trace_id": trace_id
        }
    }
    
    # Update status: generating
    yield {
        "type": "status",
        "data": "✍️ Generating answer"
    }
    
    # Step 2: Stream generation
    from rag.generate_stream import generate_answer_stream
    
    full_answer = ""
    for token in generate_answer_stream(question, research_notes, trace_id):
        full_answer += token
        yield {
            "type": "token",
            "data": token
        }
    
    # Extract final citations
    import re
    final_citations = re.findall(r'\[Doc \d+\]', full_answer)
    final_citations = list(set(final_citations))
    
    # Yield done with final answer
    yield {
        "type": "done",
        "data": {
            "answer": full_answer,
            "citations": final_citations
        }
    }
