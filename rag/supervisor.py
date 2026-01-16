from rag.state import RagState
from rag.logger import get_logger

# Phase 1 supervisor (keep for backward compatibility)
def supervisor_node(state: RagState):
    q = state["question"].lower()

    # simple routing logic (LLM-free for now)
    if any(k in q for k in ["explain", "what is", "how", "why"]):
        return {"route": "rag"}
    
    return {"route": "rag"}  # default

# Phase 3 supervisor (formalized multi-agent supervisor)
from langgraph.graph import StateGraph, END
from rag.research_team import build_research_graph
from rag.writing_team import build_writing_graph
from rag.state import AgentState

research_app = build_research_graph()
writing_app = build_writing_graph()

def supervisor_node_phase3(state: AgentState):
    """
    Supervisor node with observability and explicit state management.
    
    EXPLICIT AGENT STATE: Ensures trace_id, decision_path, used_tools, metadata_filters
    are propagated through the pipeline.
    """
    trace_id = state.get("trace_id")
    logger = get_logger(trace_id)
    
    # Ensure trace_id is set
    if not trace_id:
        import uuid
        trace_id = str(uuid.uuid4())
        state["trace_id"] = trace_id
    
    logger.info(f"Supervisor: Routing to Research Team (query: {state['question'][:50]}..., filters: {state.get('metadata_filters')})")
    logger.start_timer("supervisor_research")
    
    research_result = research_app.invoke(state)
    
    # Extract decision path and tools from research result
    decision_path = research_result.get("decision_path", "rag")
    used_tools = research_result.get("used_tools", [])
    
    logger.end_timer("supervisor_research",
                    research_notes_count=len(research_result.get("research_notes", [])),
                    tool_calls_count=len(research_result.get("tool_calls", [])),
                    decision_path=decision_path)
    
    logger.info("Supervisor: Routing to Writing Team", decision_path=decision_path)
    logger.start_timer("supervisor_writing")
    
    writing_result = writing_app.invoke(research_result)
    
    logger.end_timer("supervisor_writing",
                    answer_length=len(writing_result.get("answer", "")))
    
    # EXPLICIT AGENT STATE: Ensure all fields are in final result
    final_result = {
        **writing_result,
        "trace_id": trace_id,
        "decision_path": decision_path,
        "used_tools": used_tools,
        "metadata_filters": state.get("metadata_filters")
    }
    
    logger.info("Supervisor: Complete", 
                final_answer_length=len(writing_result.get("answer", "")),
                decision_path=decision_path)
    
    return final_result

def build_supervisor():
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node_phase3)
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", END)
    return graph.compile()
