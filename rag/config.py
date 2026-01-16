"""
Configuration management (config-driven, no hardcoded values)
Loads from config.yaml with environment variable overrides
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Load config.yaml
_config_path = Path(__file__).parent.parent / "config.yaml"
_config = {}

if _config_path.exists():
    with open(_config_path, "r") as f:
        _config = yaml.safe_load(f) or {}
else:
    # Fallback to defaults if config.yaml doesn't exist
    _config = {}

# Environment variable overrides (for deployment flexibility)
def _get_config(key_path: str, default: Any = None, env_override: str = None) -> Any:
    """Get config value, with environment variable override."""
    keys = key_path.split(".")
    value = _config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, {})
        else:
            value = default
            break
    
    if value == {}:
        value = default
    
    # Environment variable override
    if env_override and os.getenv(env_override):
        env_value = os.getenv(env_override)
        # Type coercion based on default
        if isinstance(default, bool):
            return env_value.lower() == "true"
        elif isinstance(default, int):
            return int(env_value)
        return env_value
    
    return value if value != {} else default

# LLM Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", _get_config("llm.base_url", "http://localhost:11434/api/generate"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", _get_config("llm.model", "llama3.2:latest"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", _get_config("llm.temperature", 0.0)))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", _get_config("llm.max_tokens", 2048)))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", _get_config("llm.timeout", 180)))

# Embeddings Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", _get_config("embeddings.model", "sentence-transformers/all-MiniLM-L6-v2"))

# Retrieval Configuration
TOP_K = int(os.getenv("TOP_K", _get_config("retrieval.top_k", 5)))
USE_RERANK = os.getenv("USE_RERANK", str(_get_config("retrieval.use_rerank", True))).lower() == "true"
RERANK_MODEL = os.getenv("RERANK_MODEL", _get_config("retrieval.rerank_model", "rerank-english-v3.0"))
CONTEXT_LIMIT = int(os.getenv("CONTEXT_LIMIT", _get_config("retrieval.context_limit", 2)))
RERANK_MIN_DOCS = int(os.getenv("RERANK_MIN_DOCS", _get_config("retrieval.rerank_min_docs", 3)))
RERANK_MAX_DOCS = int(os.getenv("RERANK_MAX_DOCS", _get_config("retrieval.rerank_max_docs", 10)))
RERANK_MIN_QUERY_WORDS = int(os.getenv("RERANK_MIN_QUERY_WORDS", _get_config("retrieval.rerank_min_query_words", 3)))

# Vector Database
QDRANT_URL = os.getenv("QDRANT_URL", _get_config("qdrant.url", "http://localhost:6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", _get_config("qdrant.collection_name", "demo_chunks"))

# API Keys (from environment only, never in config.yaml)
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Evaluation Gates
EVAL_FAITHFULNESS_MIN = float(os.getenv("EVAL_FAITHFULNESS_MIN", _get_config("evaluation.gates.faithfulness.min", 0.8)))
EVAL_FAITHFULNESS_BLOCK = _get_config("evaluation.gates.faithfulness.block_on_fail", True)
EVAL_PRECISION_MIN = float(os.getenv("EVAL_PRECISION_MIN", _get_config("evaluation.gates.context_precision.min", 0.9)))

# Observability
LOG_LEVEL = os.getenv("LOG_LEVEL", _get_config("observability.log_level", "INFO"))
ENABLE_STRUCTURED_LOGS = _get_config("observability.enable_structured_logs", True)
LOG_TRACE_IDS = _get_config("observability.log_trace_ids", True)
LOG_LATENCIES = _get_config("observability.log_latencies", True)
LOG_TOKEN_USAGE = _get_config("observability.log_token_usage", True)

# Production Read-Only Mode (Enterprise Security)
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", str(_get_config("production.read_only_mode", False))).lower() == "true"

# Auto-fix OLLAMA_URL if needed
if not OLLAMA_URL.endswith("/api/generate"):
    OLLAMA_URL = OLLAMA_URL.rstrip("/") + "/api/generate"
