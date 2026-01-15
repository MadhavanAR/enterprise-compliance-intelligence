from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    SparseVectorParams,
    SparseVector,
    PointStruct,
)
from rag.embeddings import embed_texts

COLLECTION_NAME = "demo_chunks"

client = QdrantClient(url="http://localhost:6333")

def create_collection(vector_size):
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams()
        }
    )

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

def store_chunks(chunks):
    dense_vectors = embed_texts(chunks)

    create_collection(len(dense_vectors[0]))

    points = []
    for idx, chunk in enumerate(chunks):
        points.append(
            PointStruct(
                id=idx,
                vector={
                    "dense": dense_vectors[idx],
                    "sparse": to_sparse(chunk)
                },
                payload={"text": chunk}
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )