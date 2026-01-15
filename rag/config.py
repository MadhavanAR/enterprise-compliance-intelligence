import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
TOP_K = int(os.getenv("TOP_K", "5"))
USE_RERANK = os.getenv("USE_RERANK", "true").lower() == "true"
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Auto-fix OLLAMA_URL if it's missing the /api/generate endpoint
if not OLLAMA_URL.endswith("/api/generate"):
    # Remove trailing slash if present, then append /api/generate
    OLLAMA_URL = OLLAMA_URL.rstrip("/") + "/api/generate"
