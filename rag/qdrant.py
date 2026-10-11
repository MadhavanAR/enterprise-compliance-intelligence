"""
Qdrant client factory (singleton).

Why this exists:
- In local mode (QdrantClient(path=...)), Qdrant enforces a single process-wide
  lock on the storage directory. Creating multiple clients in the same process
  will raise "already accessed by another instance".
- We need a single shared client for store/retrieve to keep local dev + demos
  simple and deterministic.
"""

from __future__ import annotations

from typing import Optional

from qdrant_client import QdrantClient

from rag.config import QDRANT_API_KEY, QDRANT_URL

_CLIENT: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Return a singleton Qdrant client.

    Supports:
    - Server mode: QDRANT_URL starts with http(s)://
    - Local mode:  QDRANT_URL is treated as a filesystem path
    """
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    url = str(QDRANT_URL)
    if url.startswith(("http://", "https://")):
        _CLIENT = QdrantClient(url=url, api_key=QDRANT_API_KEY, timeout=10)
    else:
        _CLIENT = QdrantClient(path=url)
    return _CLIENT

