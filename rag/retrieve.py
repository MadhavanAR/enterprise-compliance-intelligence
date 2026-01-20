from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector, Filter, FieldCondition, MatchValue
from rag.embeddings import embed_texts
from rag.store import COLLECTION_NAME
from rag.rerank import rerank, rerank_indices
from rag.config import QDRANT_URL
from rag.logger import get_logger
from typing import Optional, Dict, Any, List, TypedDict, Literal

client = QdrantClient(url=QDRANT_URL)

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

class RetrievedChunk(TypedDict, total=False):
    """Retrieved chunk with text + metadata for audit UX."""
    qdrant_id: int
    score: float
    text: str
    author: str
    source: str
    document_id: str
    vendor: str
    document_type: str
    url: str
    jurisdiction: str
    version: str

def search_docs(
    query: str,
    top_k: int = 5,
    use_rerank: bool = True,
    metadata_filters: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> List[RetrievedChunk]:
    """
    Search with strict metadata enforcement.

    Returns metadata-preserving chunks for enterprise audit UX.
    """
    logger = get_logger(trace_id)
    logger.info("Starting retrieval", query_preview=query[:80], top_k=top_k, metadata_filters=metadata_filters)

    # Build Qdrant filter from metadata
    query_filter = None
    if metadata_filters:
        filter_conditions = [
            FieldCondition(key=str(key), match=MatchValue(value=value))
            for key, value in metadata_filters.items()
        ]
        if filter_conditions:
            query_filter = Filter(must=filter_conditions)

    dense_vector = embed_texts([query])[0]
    sparse_vector = to_sparse(query)

    CANDIDATES = top_k * 3

    dense_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=dense_vector,
        using="dense",
        limit=CANDIDATES,
        with_payload=True,
        query_filter=query_filter,
    ).points

    sparse_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=sparse_vector,
        using="sparse",
        limit=CANDIDATES,
        with_payload=True,
        query_filter=query_filter,
    ).points

    merged: Dict[int, RetrievedChunk] = {}

    def _upsert(point, score: float):
        payload = point.payload or {}
        existing = merged.get(point.id)
        if existing:
            existing["score"] = float(existing.get("score", 0.0)) + float(score)
            return
        merged[point.id] = {
            "qdrant_id": int(point.id),
            "score": float(score),
            "text": payload.get("text", "") or "",
            # best-effort metadata (may not exist for legacy ingests)
            "author": payload.get("author", ""),
            "source": payload.get("source", ""),
            "document_id": payload.get("document_id", ""),
            "vendor": payload.get("vendor", ""),
            "document_type": payload.get("document_type", ""),
            "url": payload.get("url", ""),
            "jurisdiction": payload.get("jurisdiction", ""),
            "version": payload.get("version", ""),
        }

    for r in dense_res:
        _upsert(r, r.score)
    for r in sparse_res:
        _upsert(r, r.score)

    ranked = sorted(merged.values(), key=lambda x: float(x.get("score", 0.0)), reverse=True)
    candidates = [d for d in ranked[:CANDIDATES] if (d.get("text") or "").strip()]

    if metadata_filters and len(candidates) == 0:
        logger.warning("Metadata filter returned zero documents", metadata_filters=metadata_filters)
        return []

    if not use_rerank:
        return candidates[:top_k]

    texts = [d["text"] for d in candidates]
    idxs = rerank_indices(query, texts, top_k=top_k)
    reranked = [candidates[i] for i in idxs if 0 <= i < len(candidates)]
    return reranked

def search(
    query: str, 
    top_k: int = 5, 
    use_rerank: bool = True,
    metadata_filters: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
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
    docs = search_docs(
        query=query,
        top_k=top_k,
        use_rerank=use_rerank,
        metadata_filters=metadata_filters,
        trace_id=trace_id,
    )
    return [d["text"] for d in docs if (d.get("text") or "").strip()]