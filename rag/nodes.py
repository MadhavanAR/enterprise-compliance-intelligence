from rag.retrieve import search
from rag.generate import generate_answer
from rag.state import RagState
from rag.logger import logger

def retrieve_node(state: RagState) -> dict:
    logger.info("Executing retrieve node")
    docs = search(state["question"])
    logger.info(f"Retrieve node complete, {len(docs)} documents retrieved")
    return {"context": docs}

def generate_node(state: RagState) -> dict:
    logger.info("Executing generate node")
    answer = generate_answer(
        state["question"],
        state["context"]
    )
    logger.info("Generate node complete")
    return {"answer": answer}