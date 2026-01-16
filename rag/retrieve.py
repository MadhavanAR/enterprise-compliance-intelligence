from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from rag.embeddings import embed_texts
from rag.store import COLLECTION_NAME
from rag.rerank import rerank
from rag.config import QDRANT_URL
from rag.logger import logger
from typing import Optional, Dict, Any, List
from rag.metadata import format_metadata_filter

client = QdrantClient(url=QDRANT_URL)

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

def search(
    query: str, 
    top_k: int = 5, 
    use_rerank: bool = True,
    metadata_filters: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Search with strict metadata enforcement.
    
    Args:
        query: Search query
        top_k: Number of results
        use_rerank: Whether to use reranking
        metadata_filters: Metadata filters to apply (e.g., {"author": "John"})
    
    Returns:
        List of document texts (empty list if no matches and metadata filters applied)
    """
    logger.info(f"Starting retrieval for query: {query[:50]}...")
    
    # Build Qdrant filter from metadata
    query_filter = None
    if metadata_filters:
        filter_conditions = []
        for key, value in metadata_filters.items():
            filter_conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
            )
        if filter_conditions:
            query_filter = Filter(must=filter_conditions)
        logger.info(f"Metadata filters applied: {metadata_filters}")
    
    dense_vector = embed_texts([query])[0]
    sparse_vector = to_sparse(query)

    # Intentionally retrieve more candidates to simulate noisy retrieval
    CANDIDATES = top_k * 3
    logger.debug(f"Retrieving {CANDIDATES} candidates (top_k={top_k})")

    # Apply metadata filter to both queries
    dense_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=dense_vector,
        using="dense",
        limit=CANDIDATES,
        with_payload=True,
        query_filter=query_filter  # STRICT METADATA ENFORCEMENT
    ).points

    sparse_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=sparse_vector,
        using="sparse",
        limit=CANDIDATES,
        with_payload=True,
        query_filter=query_filter  # STRICT METADATA ENFORCEMENT
    ).points

    merged = {}

    for r in dense_res:
        merged[r.id] = {
            "score": r.score,
            "text": r.payload.get("text", ""),
        }

    for r in sparse_res:
        if r.id in merged:
            merged[r.id]["score"] += r.score
        else:
            merged[r.id] = {
                "score": r.score,
                "text": r.payload.get("text", ""),
            }

    ranked = sorted(
        merged.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    # Get all candidates (intentionally noisy)
    docs = [r["text"] for r in ranked[:CANDIDATES] if r["text"]]
    
    # STRICT METADATA ENFORCEMENT: If metadata filter returns zero docs, log and return empty
    if metadata_filters and len(docs) == 0:
        logger.warning(f"Metadata filter returned zero documents: {metadata_filters}")
        return []  # Hard refusal: empty list triggers "I don't know"
    
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