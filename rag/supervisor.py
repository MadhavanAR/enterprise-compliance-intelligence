from rag.state import RagState

# Phase 1 supervisor (keep for backward compatibility)
def supervisor_node(state: RagState):
    q = state["question"].lower()

    # simple routing logic (LLM-free for now)
    if any(k in q for k in ["explain", "what is", "how", "why"]):
        return {"route": "rag"}
    
    return {"route": "rag"}  # default

# Phase 2 supervisor (new multi-agent supervisor)
from rag.research_team import build_research_graph
from rag.writing_team import build_writing_graph
from rag.state import AgentState

research_app = build_research_graph()
writing_app = build_writing_graph()

def supervisor(state: AgentState):
    research_result = research_app.invoke(state)
    writing_result = writing_app.invoke({
        "research_notes": research_result["research_notes"]
    })
    return writing_result
