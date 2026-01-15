from langgraph.graph import StateGraph, END
from rag.state import AgentState
from rag.generate import generate_answer

def note_taker(state: AgentState):
    notes = "\n".join(state["research_notes"])
    return {"draft": notes}

def copy_editor(state: AgentState):
    prompt = f"""Turn these research notes into a professional LinkedIn post draft.

Research Notes:
{state["draft"]}

Write a clear, informative LinkedIn post based on these notes."""
    
    draft = generate_answer(
        prompt,
        [state["draft"]]
    )
    return {"draft": draft}

def dopeness_editor(state: AgentState):
    prompt = f"""Make this LinkedIn post more engaging by adding emojis and relevant hashtags.

Post Draft:
{state["draft"]}

Enhance this post with appropriate emojis and hashtags while keeping the content professional."""
    
    final = generate_answer(
        prompt,
        [state["draft"]]
    )
    return {"final_post": final}

def build_writing_graph():
    graph = StateGraph(AgentState)
    graph.add_node("notes", note_taker)
    graph.add_node("edit", copy_editor)
    graph.add_node("dope", dopeness_editor)

    graph.set_entry_point("notes")
    graph.add_edge("notes", "edit")
    graph.add_edge("edit", "dope")
    graph.add_edge("dope", END)

    return graph.compile()
