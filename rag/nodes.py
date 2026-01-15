from rag.retrieve import search
from rag.generate import generate_answer
from rag.state import RagState

def retrieve_node(state: RagState) -> dict:
    docs = search(state["question"])
    return {"context": docs}

def generate_node(state: RagState) -> dict:
    answer = generate_answer(
        state["question"],
        state["context"]
    )
    return {"answer": answer}