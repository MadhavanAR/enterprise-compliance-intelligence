from langgraph.graph import StateGraph, END
from rag.state import RagState
from rag.nodes import retrieve_node, generate_node

workflow = StateGraph(RagState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()