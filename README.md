# Production RAG Platform

Retrieval-Augmented Generation platform for document processing and querying.

## Run

1. Start Qdrant
2. Start Ollama
3. `python main.py`

## Architecture

- Hybrid retrieval (dense + BM25)
- Cohere reranking
- LangGraph orchestration
- Local LLM (Ollama)
- Git-based evaluation
