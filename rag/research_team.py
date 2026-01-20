import asyncio
from langgraph.graph import StateGraph, END
from rag.state import AgentState
from rag.retrieve import search, search_docs  # metadata-preserving retrieval
from rag.mcp_client import call_tool  # Keep sync for now (can be async later)
from rag.logger import get_logger

def needs_web_search(question: str) -> bool:
    """Determine if query needs live/current information via web_search."""
    keywords = ["today", "latest", "current", "won", "score", "news", "2025", "stanley cup", "who won", "what happened", "recent"]
    return any(k in question.lower() for k in keywords)

def needs_dice_roll(question: str) -> bool:
    """Determine if query needs calculation/randomness via roll_dice."""
    keywords = ["roll", "dice", "damage", "d20", "d6", "random"]
    return any(k in question.lower() for k in keywords)

def research_node(state: AgentState) -> dict:
    """
    Research node - intelligently routes to MCP tools or RAG.
    
    Decision rules:
    - If query needs live/current info → web_search
    - If query needs calculation/randomness → roll_dice
    - Else → use RAG retrieval
    
    STRICT METADATA ENFORCEMENT: Applies metadata_filters to RAG retrieval.
    HARD REFUSAL: Returns empty notes if metadata filter yields zero docs.
    """
    trace_id = state.get("trace_id")
    logger = get_logger(trace_id)
    
    question = state["question"]
    metadata_filters = state.get("metadata_filters")  # Extract metadata filters
    notes = []
    documents = []
    tool_calls = state.get("tool_calls", [])
    used_tools = []
    decision_path = "rag"  # Default
    
    logger.start_timer("research")
    
    if needs_web_search(question):
        logger.info("Decision: Using MCP tool web_search", decision_path="web_search")
        logger.start_timer("mcp_web_search")
        try:
            result = call_tool("web_search", {"query": question})
            # Improved parsing: check for verified answer
            if result.get("has_verified_answer", False):
                notes.append(result["result"])
            else:
                # No verified answer - mark explicitly
                logger.info("Web search returned no verified answer")
                notes.append(result["result"])  # Still include for transparency
            tool_calls.append({"tool": "web_search", "query": question})
            used_tools.append("web_search")
            logger.end_timer("mcp_web_search", result_length=len(result.get("result", "")))
        except Exception as e:
            logger.error("Tool error, falling back to RAG", error=str(e))
            # Fallback to RAG with metadata filters
            docs = search(question, metadata_filters=metadata_filters)
            notes.extend(docs)
    elif needs_dice_roll(question):
        decision_path = "roll_dice"
        logger.info("Decision: Using MCP tool roll_dice", decision_path=decision_path)
        logger.start_timer("mcp_roll_dice")
        try:
            # Extract dice parameters (simple heuristic)
            sides = 6
            count = 1
            question_lower = question.lower()
            if "d20" in question_lower or "20-sided" in question_lower:
                sides = 20
            if "d6" in question_lower or "6-sided" in question_lower:
                sides = 6
            if "4d" in question_lower or "four" in question_lower:
                count = 4
            elif "2d" in question_lower or "two" in question_lower:
                count = 2
            
            dice_result = call_tool("roll_dice", {"sides": sides, "count": count})
            result_text = f"Dice roll: {dice_result['results']} (total: {dice_result['total']})"
            notes.append(result_text)
            tool_calls.append({"tool": "roll_dice", "sides": sides, "count": count})
            used_tools.append("roll_dice")
            logger.end_timer("mcp_roll_dice", total=dice_result.get("total"))
        except Exception as e:
            logger.error("Tool error, falling back to RAG", error=str(e))
            # Fallback to RAG with metadata filters
            docs = search(question, metadata_filters=metadata_filters)
            notes.extend(docs)
    else:
        decision_path = "rag"
        logger.info(f"Decision: Using RAG retrieval (path: {decision_path}, filters: {metadata_filters})")
        logger.start_timer("rag_retrieval")
        # STRICT METADATA ENFORCEMENT + METADATA PRESERVATION
        retrieved = search_docs(question, metadata_filters=metadata_filters, trace_id=trace_id)
        documents = retrieved
        docs_text = [d.get("text", "") for d in retrieved if isinstance(d, dict)]
        notes.extend([t for t in docs_text if isinstance(t, str) and t.strip()])
        logger.end_timer("rag_retrieval", docs_retrieved=len(notes))
        
        # Log if metadata filter resulted in zero docs
        if metadata_filters and len(docs) == 0:
            logger.warning(f"Metadata filter returned zero documents - will trigger hard refusal: {metadata_filters}")
    
    logger.end_timer("research", notes_count=len(notes), tool_calls_count=len(tool_calls))
    
    # EXPLICIT AGENT STATE: Include all required fields
    return {
        "research_notes": notes,
        "context": notes,  # Keep context in sync
        "documents": documents,
        "tool_calls": tool_calls,
        "trace_id": trace_id,  # Propagate trace_id
        "decision_path": decision_path,  # Explicit decision path
        "used_tools": used_tools,  # List of tools invoked
        "metadata_filters": metadata_filters  # Propagate filters
    }

def build_research_graph():
    graph = StateGraph(AgentState)
    graph.add_node("researcher", research_node)
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", END)
    return graph.compile()
