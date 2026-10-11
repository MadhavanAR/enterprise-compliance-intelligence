from langgraph.graph import StateGraph, END
from rag.state import AgentState
from rag.generate import generate_answer
from rag.generate_grounded import generate_grounded_answer
from rag.confidence import estimate_confidence
from rag.logger import get_logger

def note_taker(state: AgentState):
    return {"research_notes": state["context"]}

def copy_editor(state: AgentState):
    return {"research_notes": state["research_notes"]}

def dopeness_editor(state: AgentState):
    """
    Generate grounded answer with structured claims + citations.
    Uses grounded answer generation for enterprise-grade output.
    """
    trace_id = state.get("trace_id")
    logger = get_logger(trace_id)
    ff = state.get("feature_flags")

    logger.start_timer("writing")

    grounded_result = generate_grounded_answer(
        state["question"],
        state["research_notes"],
        trace_id=trace_id,
        feature_flags=ff,
    )
    answer = grounded_result.get("answer", "")
    claims = grounded_result.get("claims", [])
    sources_used = grounded_result.get("sources_used", [])

    if ff and getattr(ff, "enable_confidence", True) is False:
        confidence = None
        confidence_reason = "disabled (demo mode)"
    else:
        metadata_match = state.get("metadata_filters") is not None and len(sources_used) > 0
        rerank_score_avg = state.get("rerank_score_avg")
        confidence_result = estimate_confidence(
            claims_count=len(claims),
            sources_used=len(sources_used),
            metadata_match=metadata_match,
            rerank_score_avg=rerank_score_avg,
            trace_id=trace_id,
        )
        confidence = confidence_result.get("confidence", 0.5)
        confidence_reason = confidence_result.get("confidence_reason", "")

    logger.end_timer("writing", answer_length=len(answer), claims_count=len(claims), sources_count=len(sources_used), confidence=confidence)

    out = {
        "answer": answer,
        "claims": claims,
        "sources_used": sources_used,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "unverified": grounded_result.get("unverified", False),
    }
    if grounded_result.get("generation_error"):
        out["generation_error"] = grounded_result["generation_error"]
    return out

def build_writing_graph():
    graph = StateGraph(AgentState)
    graph.add_node("note_taker", note_taker)
    graph.add_node("copy_editor", copy_editor)
    graph.add_node("dopeness_editor", dopeness_editor)

    graph.set_entry_point("note_taker")
    graph.add_edge("note_taker", "copy_editor")
    graph.add_edge("copy_editor", "dopeness_editor")
    graph.add_edge("dopeness_editor", END)

    return graph.compile()
