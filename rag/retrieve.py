from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector
from rag.embeddings import embed_texts
from rag.store import COLLECTION_NAME
from rag.rerank import rerank
from rag.generate import generate_answer

client = QdrantClient(url="http://localhost:6333")

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

def search(query: str, top_k: int = 5):
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
    reranked_docs = rerank(query, docs, top_k=top_k)

    # Display retrieved documents
    print(f"\nQuery: {query}\n")
    print("=" * 60)
    print("RETRIEVED DOCUMENTS (after reranking):")
    print("=" * 60)
    for i, doc in enumerate(reranked_docs, 1):
        print(f"\n--- Document {i} ---")
        print(doc[:500] + ("..." if len(doc) > 500 else ""))
        print()

    # 🔑 LLM GENERATION (with error handling)
    try:
        answer = generate_answer(query, reranked_docs)
        print("=" * 60)
        print("FINAL ANSWER")
        print("=" * 60)
        print(answer)
    except (RuntimeError, ValueError) as e:
        print("=" * 60)
        print("GENERATION SKIPPED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print("\nNote: Retrieved documents are shown above. Please fix API configuration to enable answer generation.")

if __name__ == "__main__":
    search("BM25 keyword search in RAG")