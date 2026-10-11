"""
Security utilities, rate limiting, and administrative access controls.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Header, HTTPException, Request, status

# Rate limiter settings
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# In-memory sliding window rate tracker: ip -> list of timestamps
_request_records: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """
    Sliding-window per-client IP rate limiter.
    Raises HTTP 429 when threshold is exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    # Respect Forwarded / X-Forwarded-For if behind trusted proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    now = time.time()
    window_start = now - 60.0

    # Prune old timestamps
    timestamps = [t for t in _request_records[client_ip] if t > window_start]
    _request_records[client_ip] = timestamps

    if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit of {RATE_LIMIT_PER_MINUTE} requests/minute exceeded. Please retry later.",
                "retry_after_seconds": int(60 - (now - timestamps[0])),
            },
        )

    _request_records[client_ip].append(now)


def verify_admin_key(
    x_admin_key: str = Header(default="", alias="X-Admin-Key")
) -> None:
    """
    Verify administrative access key for ingestion/corpus modification endpoints.
    Fails closed if ADMIN_API_KEY is unset or key does not match.
    """
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ingestion_disabled",
                "message": "Administrative operations are disabled because no ADMIN_API_KEY is configured on this deployment.",
            },
        )

    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "message": "Invalid or missing administrative credentials.",
            },
        )
