from typing import TypedDict, List, Literal

# Phase 1 state (keep for backward compatibility)
class RagState(TypedDict):
    question: str
    context: List[str]
    answer: str
    route: Literal["rag", "end"]

# Phase 2 state (new agent state)
class AgentState(TypedDict):
    question: str
    research_notes: List[str]
    draft: str
    final_post: str
    next: str
