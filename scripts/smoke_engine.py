"""
Run a few questions through the canonical engine and print the raw payloads.

Usage:
    python scripts/smoke_engine.py ["question" ...]

Requires the configured Qdrant index and Ollama endpoint to be reachable.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from rag.engine import run_enterprise_query  # noqa: E402

DEFAULT_QUESTIONS = [
    "Which compliance programs does AWS maintain to help customers satisfy regulatory requirements?",
    "How do customers access AWS compliance reports?",
    "What is the AWS data retention period for deleted S3 objects?",
    "What do you think about AI safety?",
]


def main() -> None:
    questions = sys.argv[1:] or DEFAULT_QUESTIONS
    for q in questions:
        started = time.time()
        result = run_enterprise_query(q)
        elapsed = time.time() - started
        print("=" * 80)
        print(f"Q: {q}  ({elapsed:.1f}s)")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
