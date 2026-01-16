from typing import TypedDict, List, Literal, Optional, Dict, Any

# Phase 1 state (keep for backward compatibility)
class RagState(TypedDict):
    question: str
    context: List[str]
    answer: str
    route: Literal["rag", "end"]

# Phase 3 state (formalized agent state with explicit fields)
class AgentState(TypedDict, total=False):
    question: str
    research_notes: List[str]
    context: List[str]
    answer: str
    tool_calls: List[dict]  # Track MCP tool usage
    trace_id: Optional[str]  # Request tracking
    decision_path: Optional[str]  # "rag" | "web_search" | "roll_dice"
    used_tools: List[str]  # List of tools invoked
    metadata_filters: Optional[Dict[str, Any]]  # Metadata filters applied
