#!/usr/bin/env python3
"""
Seed and verify compliance document corpus into Qdrant.

Usage:
    python scripts/ingest_documents.py

Supports:
- Local embedded Qdrant (QDRANT_URL=.qdrant_local)
- Remote Qdrant / Qdrant Cloud (QDRANT_URL=https://... with QDRANT_API_KEY)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from rag.config import COLLECTION_NAME, QDRANT_URL
from rag.ingest import load_and_chunk
from rag.logger import get_logger
from rag.qdrant import get_qdrant_client
from rag.store import store_chunks


def main():
    logger = get_logger("seed-corpus")
    data_dir = Path(__file__).resolve().parent.parent / "data"

    print("=" * 70)
    print("ENTERPRISE COMPLIANCE INTELLIGENCE: CORPUS SEEDING")
    print(f"Target Qdrant: {QDRANT_URL}")
    print(f"Target Collection: {COLLECTION_NAME}")
    print("=" * 70)

    all_chunks = []

    # 1. Ingest AWS Compliance document
    aws_file = data_dir / "aws_compliance.txt"
    if aws_file.exists():
        print(f"Loading {aws_file.name}...")
        aws_chunks = load_and_chunk(
            file_path=str(aws_file),
            author="Amazon Web Services",
            source="aws_compliance_programs",
            document_id="aws_compliance",
            version="2025-01",
        )
        for _, meta in aws_chunks:
            meta["vendor"] = "AWS"
            meta["title"] = "AWS Compliance Programs"
            meta["document_type"] = "compliance_overview"
            meta["url"] = "https://aws.amazon.com/compliance/programs/"
            meta["jurisdiction"] = "global"
        all_chunks.extend(aws_chunks)
        print(f"  -> Generated {len(aws_chunks)} chunks.")

    # 2. Ingest RAG Best Practices document
    sample_file = data_dir / "sample_doc.txt"
    if sample_file.exists():
        print(f"Loading {sample_file.name}...")
        rag_chunks = load_and_chunk(
            file_path=str(sample_file),
            author="Internal AI Platform Team",
            source="rag_best_practices",
            document_id="rag_best_practices",
            version="2024-11",
        )
        for _, meta in rag_chunks:
            meta["vendor"] = "Internal AI Platform"
            meta["title"] = "Retrieval-Augmented Generation Best Practices"
            meta["document_type"] = "technical_standard"
            meta["jurisdiction"] = "internal"
        all_chunks.extend(rag_chunks)
        print(f"  -> Generated {len(rag_chunks)} chunks.")

    if not all_chunks:
        print("ERROR: No documents found to ingest.")
        sys.exit(1)

    print(f"\nIndexing total of {len(all_chunks)} chunks into '{COLLECTION_NAME}'...")
    store_chunks(all_chunks)

    # Verification scroll
    client = get_qdrant_client()
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )
    print(f"\nVerification successful! {len(points)} points confirmed in '{COLLECTION_NAME}'.")
    for pt in points:
        doc_id = (pt.payload or {}).get("document_id")
        title = (pt.payload or {}).get("title")
        print(f"  • Point {pt.id}: [{doc_id}] {title}")

    print("\n✅ Corpus ingestion and verification complete!")


if __name__ == "__main__":
    main()
