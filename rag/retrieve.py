from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector
from rag.embeddings import embed_texts
from rag.store import COLLECTION_NAME
from rag.rerank import rerank
from rag.config import QDRANT_URL
from rag.logger import logger

client = QdrantClient(url=QDRANT_URL)

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

def search(query: str, top_k: int = 5, use_rerank: bool = True) -> list[str]:
    logger.info(f"Starting retrieval for query: {query[:50]}...")
    dense_vector = embed_texts([query])[0]
    sparse_vector = to_sparse(query)

    # Intentionally retrieve more candidates to simulate noisy retrieval
    CANDIDATES = top_k * 3
    logger.debug(f"Retrieving {CANDIDATES} candidates (top_k={top_k})")

    dense_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=dense_vector,
        using="dense",
        limit=CANDIDATES,
        with_payload=True,
    ).points

    sparse_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=sparse_vector,
        using="sparse",
        limit=CANDIDATES,
        with_payload=True,
    ).points

    merged = {}

    for r in dense_res:
        merged[r.id] = {
            "score": r.score,
            "text": r.payload["text"],
        }

    for r in sparse_res:
        if r.id in merged:
            merged[r.id]["score"] += r.score
        else:
            merged[r.id] = {
                "score": r.score,
                "text": r.payload["text"],
            }

    ranked = sorted(
        merged.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    # Get all candidates (intentionally noisy)
    docs = [r["text"] for r in ranked[:CANDIDATES]]
    logger.info(f"Retrieved {len(docs)} candidate documents")

    if use_rerank:
        logger.info("Applying reranking")
        # Reranker selects best top_k from larger candidate pool
        reranked = rerank(query, docs, top_k=top_k)
        logger.info(f"Reranking complete, returning {len(reranked)} documents")
        return reranked

    # Without rerank, just return first top_k
    logger.info(f"Returning top {top_k} documents without reranking")
    return docs[:top_k]