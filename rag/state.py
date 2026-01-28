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
    decision_path: Optional[str]  # "rag" | "web_search" | "roll_dice" | List[str]
    used_tools: List[str]  # List of tools invoked
    metadata_filters: Optional[Dict[str, Any]]  # Metadata filters applied
    documents: List[Dict[str, Any]]  # Retrieved docs with metadata (for audit UX)
    # Enterprise-grade grounded answer fields
    claims: List[Dict[str, str]]  # Structured claims with source_doc
    sources_used: List[str]  # List of source document IDs
    confidence: float  # Confidence score 0.0-1.0
    confidence_reason: str  # Reason for confidence score
    intent: str  # Query intent: "factual" | "analytical" | "opinion" | "unknown"
    confidence_requirement: str  # "high" | "medium" | "low"
    feature_flags: Optional[Any]  # DEMO-ONLY: Compare Mode toggles (canonical: engine only)
