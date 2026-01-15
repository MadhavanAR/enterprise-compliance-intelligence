from qdrant_client import QdrantClient
from rag.embeddings import embed_texts
from rag.store import COLLECTION_NAME

client = QdrantClient(url="http://localhost:6333")

def search(query: str, top_k: int = 5):
    query_vector = embed_texts([query])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True
    )

    print(f"\nQuery: {query}\n")
    for i, res in enumerate(results.points):
        print(f"--- Result {i+1} (score: {res.score:.4f}) ---")
        print(res.payload["text"][:300])
        print()

if __name__ == "__main__":
    search("What breaks RAG systems?")