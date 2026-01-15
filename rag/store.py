from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from rag.embeddings import embed_texts

COLLECTION_NAME = "demo_chunks"

client = QdrantClient(url="http://localhost:6333")

def create_collection(vector_size):
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

def store_chunks(chunks):
    vectors = embed_texts(chunks)
    create_collection(len(vectors[0]))

    client.upload_collection(
        collection_name=COLLECTION_NAME,
        vectors=vectors,
        payload=[{"text": c} for c in chunks],
        ids=list(range(len(chunks)))
    )