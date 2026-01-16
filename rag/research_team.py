from langgraph.graph import StateGraph, END
from rag.state import AgentState
from rag.retrieve import search
from rag.mcp_client import call_tool
from rag.logger import logger

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
    """
    question = state["question"]
    notes = []
    tool_calls = state.get("tool_calls", [])
    
    if needs_web_search(question):
        logger.info("Calling MCP tool: web_search")
        try:
            result = call_tool("web_search", {"query": question})
            notes.append(result["result"])
            tool_calls.append({"tool": "web_search", "query": question})
            logger.info("Web search completed")
        except Exception as e:
            logger.error(f"Tool error: {e}")
            # Fallback to RAG
            docs = search(question)
            notes.extend(docs)
    elif needs_dice_roll(question):
        logger.info("Calling MCP tool: roll_dice")
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
            logger.info("Dice roll completed")
        except Exception as e:
            logger.error(f"Tool error: {e}")
            # Fallback to RAG
            docs = search(question)
            notes.extend(docs)
    else:
        logger.info("Using RAG retrieval")
        docs = search(question)
        notes.extend(docs)
    
    logger.info(f"Research notes collected: {len(notes)} items")
    return {
        "research_notes": notes,
        "context": notes,  # Keep context in sync
        "tool_calls": tool_calls
    }

def build_research_graph():
    graph = StateGraph(AgentState)
    graph.add_node("researcher", research_node)
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", END)
    return graph.compile()
