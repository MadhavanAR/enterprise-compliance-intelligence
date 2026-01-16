from typing import TypedDict, List, Literal

# Phase 1 state (keep for backward compatibility)
class RagState(TypedDict):
    question: str
    context: List[str]
    answer: str
    route: Literal["rag", "end"]

# Phase 3 state (formalized agent state)
class AgentState(TypedDict):
    question: str
    research_notes: List[str]
    context: List[str]
    answer: str
    tool_calls: List[dict]  # Track MCP tool usage
