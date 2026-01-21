"""
Embeddings (dense vectors) for retrieval.

Enterprise constraints:
- Deterministic
- Offline-safe (must not require network at runtime)
- Fail-closed by default (callers decide fallback strategy)
"""

from __future__ import annotations

import os
from typing import List, Optional

from rag.config import EMBEDDING_MODEL
from rag.logger import get_logger

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


_MODEL: Optional["SentenceTransformer"] = None
_MODEL_LOAD_ERROR: Optional[BaseException] = None


def _force_offline_mode() -> None:
    """
    Prevent any HuggingFace hub network calls.

    This keeps the platform runnable in locked-down enterprise environments
    and also avoids failures in network-restricted sandboxes.
    """
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def _get_model(trace_id: Optional[str] = None) -> "SentenceTransformer":
    global _MODEL, _MODEL_LOAD_ERROR

    if _MODEL is not None:
        return _MODEL

    if _MODEL_LOAD_ERROR is not None:
        raise RuntimeError("Embedding model previously failed to load") from _MODEL_LOAD_ERROR

    if SentenceTransformer is None:
        _MODEL_LOAD_ERROR = RuntimeError("sentence-transformers is not installed")
        raise RuntimeError("Dense embeddings unavailable (sentence-transformers missing)") from _MODEL_LOAD_ERROR

    _force_offline_mode()
    logger = get_logger(trace_id)

    try:
        # Important: do not trigger any hub downloads at runtime.
        _MODEL = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded (offline)", embedding_model=EMBEDDING_MODEL)
        return _MODEL
    except BaseException as e:  # pragma: no cover
        _MODEL_LOAD_ERROR = e
        logger.error(
            "Embedding model unavailable; dense retrieval disabled",
            embedding_model=EMBEDDING_MODEL,
            error_type=type(e).__name__,
        )
        raise RuntimeError("Dense embeddings unavailable (model not cached / load failed)") from e


def embed_texts(texts: List[str], trace_id: Optional[str] = None) -> List[List[float]]:
    """
    Embed texts into dense vectors.

    Raises RuntimeError if dense embeddings are unavailable in the current environment.
    Callers that can operate in sparse-only mode should catch and fall back safely.
    """
    model = _get_model(trace_id=trace_id)
    vectors = model.encode(texts)
    return vectors.tolist()