# Enterprise Compliance Intelligence

Document-grounded Q&A for compliance and policy. Answers are tied to sources; unanswerable questions get a refusal. Auditable (claims, sources, decision path, confidence).

**Presentation:** [From POC to Production: Reliable RAG Systems in 2026](https://from-poc-to-production-r-5go3y0y.gamma.site/)

**Prerequisites:** Python 3.10+, Ollama, Qdrant. Optional: Cohere API key for reranking.

**Install**

```bash
git clone <https://github.com/MadhavanAR/ECI.git>
cd ECI
pip install -r requirements.txt
cp .env.example .env   # set Qdrant URL, Ollama URL, optional Cohere key
```

**Run dependencies**

```bash
docker run -p 6333:6333 qdrant/qdrant
ollama serve && ollama pull llama3.2:latest
```

**Ingest**

```bash
python -m rag.ingest
```

**Use**

```bash
# CLI
python main.py "Your question"

# Web UI
streamlit run ui.py
```

```python
# Programmatic
from rag.engine import run_enterprise_query
r = run_enterprise_query("Your question")
# r["answer"], r["claims"], r["sources_used"], r["decision_path"], r["confidence"]
```

**Code structure**

```
rag-platform/
├── main.py              # CLI: runs a single query
├── ui.py                # Streamlit UI (chat + audit panel)
├── app.py               # Alternate app entry
├── config.py            # Loads config.yaml and env
├── state.py             # App-level state
├── config.yaml          # LLM, retrieval, Qdrant, evaluation
├── .env.example         # Env vars (Qdrant URL, Ollama, Cohere)
│
├── rag/                 # Core RAG pipeline
│   ├── engine.py        # Single entry: run_enterprise_query() -> answer, claims, sources, decision_path, confidence
│   ├── explain.py       # explain_response(result) -> audit view of same payload
│   ├── supervisor.py    # Orchestrates router -> research -> writing
│   ├── query_router.py  # Intent / routing
│   ├── research_team.py # Retrieval (hybrid + optional rerank)
│   ├── writing_team.py  # Grounded answer + claims + citations
│   ├── generate_grounded.py  # Structured generation, refusal, claim-to-source
│   ├── retrieve.py      # Dense + sparse retrieval
│   ├── rerank.py        # Cohere rerank
│   ├── confidence.py    # Evidence-based confidence score
│   ├── ingest.py        # Ingest docs into Qdrant
│   ├── embeddings.py    # Sentence-transformers
│   ├── qdrant.py        # Vector store client
│   ├── metadata.py     # Metadata filtering
│   ├── feature_flags.py # Demo toggles (visibility only in UI)
│   ├── generate_ui.py   # Streaming + metadata for UI
│   └── prompts/         # LLM prompts (grounded answer, router, confidence)
│
├── eval/                # Evaluation
│   ├── run_ragas.py     # RAGAS metrics (faithfulness, precision, recall)
│   └── gates.py        # Quality gates from config
│
├── demos/               # Scripts: refusal, confidence, audit trail
├── pages/               # Streamlit pages (e.g. Documentation)
├── mcp/                 # MCP server (optional tools)
└── data/                # Sample documents for ingest
```

**License:** MIT. See [LICENSE](LICENSE).
