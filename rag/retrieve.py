from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector
from rag.embeddings import embed_texts
from rag.store import COLLECTION_NAME
from rag.rerank import rerank

client = QdrantClient(url="http://localhost:6333")

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

def search(query: str, top_k: int = 5) -> list[str]:
    dense_vector = embed_texts([query])[0]
    sparse_vector = to_sparse(query)

    dense_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=dense_vector,
        using="dense",
        limit=top_k,
        with_payload=True,
    ).points

    sparse_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=sparse_vector,
        using="sparse",
        limit=top_k,
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

    docs = [r["text"] for r in ranked[:top_k]]

    # 🔑 RERANK
    reranked_docs = rerank(query, docs, top_k=top_k)

    return reranked_docs