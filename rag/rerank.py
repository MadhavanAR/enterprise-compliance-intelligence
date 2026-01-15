# Document reranking module
import cohere
from rag.config import COHERE_API_KEY
from rag.logger import logger

_cohere_client = None

def _get_client():
    """Lazy initialization of Cohere client."""
    global _cohere_client
    if _cohere_client is None:
        if not COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY environment variable not set")
        _cohere_client = cohere.Client(COHERE_API_KEY)
    return _cohere_client

def rerank(query: str, docs: list[str], top_k: int = 5):
    logger.info(f"Reranking {len(docs)} documents, selecting top {top_k}")
    co = _get_client()
    res = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=docs,
        top_n=top_k,
    )
    reranked = [docs[r.index] for r in res.results]
    logger.info(f"Reranking complete, selected {len(reranked)} documents")
    return reranked