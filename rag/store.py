from collections import Counter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    SparseVectorParams,
    SparseVector,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from rag.embeddings import embed_texts
from rag.config import QDRANT_URL
from rag.logger import logger
from typing import List, Tuple, Dict, Any, Optional

COLLECTION_NAME = "demo_chunks"

client = QdrantClient(url=QDRANT_URL)

def create_collection(vector_size):
    logger.info(f"Creating collection '{COLLECTION_NAME}' with vector size {vector_size}")
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
    logger.info(f"Collection '{COLLECTION_NAME}' created successfully")

def to_sparse(text: str):
    counts = Counter(text.lower().split())
    return SparseVector(
        indices=list(range(len(counts))),
        values=list(counts.values())
    )

def store_chunks(chunks: List[Tuple[str, Dict[str, Any]]]):
    """
    Store chunks with metadata.
    
    Args:
        chunks: List of (chunk_text, metadata) tuples
    """
    # Handle backward compatibility (plain list of strings)
    if chunks and isinstance(chunks[0], str):
        logger.warning("Legacy format detected: storing chunks without metadata")
        chunks = [(chunk, {"author": "unknown", "source": "unknown", "document_id": "unknown"}) 
                 for chunk in chunks]
    
    logger.info(f"Storing {len(chunks)} chunks in Qdrant with metadata")
    
    chunk_texts = [chunk for chunk, _ in chunks]
    dense_vectors = embed_texts(chunk_texts)

    create_collection(len(dense_vectors[0]))

    points = []
    for idx, (chunk, metadata) in enumerate(chunks):
        # Payload includes both text and metadata
        payload = {
            "text": chunk,
            **metadata  # Spread metadata into payload
        }
        
        points.append(
            PointStruct(
                id=idx,
                vector={
                    "dense": dense_vectors[idx],
                    "sparse": to_sparse(chunk)
                },
                payload=payload
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    logger.info(f"Successfully stored {len(points)} points in collection '{COLLECTION_NAME}' with metadata")