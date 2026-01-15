import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
TOP_K = int(os.getenv("TOP_K", "5"))
USE_RERANK = os.getenv("USE_RERANK", "true").lower() == "true"
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
