from langgraph.graph import StateGraph, END
from rag.state import AgentState
from rag.generate import generate_answer
from rag.logger import get_logger

def note_taker(state: AgentState):
    return {"research_notes": state["context"]}

def copy_editor(state: AgentState):
    return {"research_notes": state["research_notes"]}

def dopeness_editor(state: AgentState):
    trace_id = state.get("trace_id")
    logger = get_logger(trace_id)
    
    logger.start_timer("writing")
    answer = generate_answer(
        state["question"],
        state["research_notes"],
        trace_id=trace_id
    )
    logger.end_timer("writing", answer_length=len(answer))
    return {"answer": answer}

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
