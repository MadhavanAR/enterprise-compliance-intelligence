from langgraph.graph import StateGraph, END
from rag.state import AgentState
from rag.retrieve import search

def research_node(state: AgentState):
    query = state["question"]
    docs = search(query)
    notes = [doc[:300] for doc in docs]

    return {
        "research_notes": notes,
        "next": "DONE"
    }

def build_research_graph():
    graph = StateGraph(AgentState)
    graph.add_node("research", research_node)
    graph.set_entry_point("research")
    graph.add_edge("research", END)
    return graph.compile()
