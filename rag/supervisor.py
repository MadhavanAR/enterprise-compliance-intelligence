def supervisor_node(state):
    q = state["question"].lower()

    # simple routing logic (LLM-free for now)
    if any(k in q for k in ["explain", "what is", "how", "why"]):
        return {"route": "rag"}
    
    return {"route": "rag"}  # default