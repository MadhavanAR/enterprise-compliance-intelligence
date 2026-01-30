# Enterprise Compliance Intelligence

A deterministic, document-grounded question-answering system for compliance and policy questions. Answers are traceable to source documents, refusal-capable when evidence is insufficient and designed for audit and regulatory use. This is not a general-purpose chatbot.

---

## Overview

The system answers questions using only your ingested documents. When it cannot support an answer from those sources, it responds with a refusal ("I don't know") instead of guessing. Every answer can be audited: claims are linked to sources, decision paths are logged and confidence is scored from evidence strength.

**Key properties:**

- **Document-grounded:** Answers are derived only from retrieved context; no unsupported claims.
- **Refusal-capable:** Unanswerable or unsupported questions receive an explicit refusal.
- **Auditable:** Trace IDs, decision paths, claims-to-sources mapping, and confidence reasoning are available via a single engine API and optional explain/audit API.
- **Deterministic:** Temperature is set to zero; configuration drives behavior.

---

## Intended audience

**Suitable for:**

- Technical and compliance leads evaluating RAG for policy or compliance use
- Teams that need source-linked answers and explicit refusals
- Environments where audit trails and evidence strength matter

**Not suitable for:**

- General conversational or consumer chatbots
- Purely experimental or non-audited use cases
- Workloads that require answers without document support

---

## Safety and compliance

**Refusal and grounding**

- Empty or irrelevant context leads to refusal; the model is not called without usable context.
- Structured claims require source references; enforcement is in code and prompts.
- Capability-style questions (e.g. "Can I...", "Does X allow...") are answered only when the context contains explicit guarantees; otherwise a qualified, document-scoped statement or refusal is returned.

**Auditability**

- Each request has a trace ID.
- Decision path (e.g. router, retrieval, generation) is recorded.
- Claims are mapped to source documents.
- Confidence and refusal reasons are exposed in the response and explain API.

**Determinism and configuration**

- LLM temperature is 0.
- Retrieval, reranking, and generation are config-driven (see `config.yaml` and `.env.example`).

---

## Architecture

High-level flow:

```
Query -> Query Router -> Research (retrieval) -> Writing (grounded generation) -> Answer + claims + sources
```

**Components**

- **Engine** (`rag/engine.py`): Single entry point for CLI, UI, and API. Returns a stable payload: answer, claims, sources_used, decision_path, confidence, refusal_reason (when applicable).
- **Query router:** Classifies intent and routes to retrieval (or other paths if extended).
- **Research team:** Hybrid retrieval (dense + sparse), optional rerank, metadata filtering.
- **Writing team:** Grounded answer generation with structured claims and citations.
- **Confidence:** Score derived from evidence (e.g. source count, claim coverage), not model certainty.
- **Explain API** (`rag/explain.py`): Audit-oriented view of the same response (trace_id, decision_path, claims, sources_used, confidence, refusal_reason).

---

## Prerequisites

- Python 3.10+
- Ollama (local LLM)
- Qdrant (vector store)

Optional: Cohere API key for reranking (see `.env.example`).

---

## Installation

```bash
git clone <repository-url>
cd rag-platform

pip install -r requirements.txt
```

Copy environment defaults and set as needed:

```bash
cp .env.example .env
# Edit .env for Qdrant URL, Ollama base URL, optional Cohere key, etc.
```

Start dependencies:

```bash
# Qdrant (example with Docker)
docker run -p 6333:6333 qdrant/qdrant

# Ollama
ollama serve
ollama pull llama3.2:latest
```

Ingest documents (paths and collection name are configurable):

```bash
python -m rag.ingest
```

---

## Quick start

**CLI (single query)**

```bash
python main.py "What compliance certifications does the documentation describe?"
```

**Programmatic (engine only)**

```python
from rag.engine import run_enterprise_query

result = run_enterprise_query("What does the documentation say about access controls?")

print(result["answer"])
print(result["claims"])
print(result["sources_used"])
print(result["decision_path"])
print(result["confidence"])
# result["refusal_reason"] when the answer is a refusal
```

**Web UI**

```bash
streamlit run ui.py
```

The UI shows the answer and an optional audit panel (claims, sources, decision path, confidence). Toggles control visibility only; the backend always returns the full payload.

---

## Project structure

```
rag-platform/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── main.py              # CLI entry
├── app.py                # Alternate app entry
├── ui.py                 # Streamlit UI
├── config.py             # Config loading
├── state.py              # App state
├── rag/
│   ├── engine.py         # Canonical query entry (run_enterprise_query)
│   ├── explain.py        # Audit/explain API
│   ├── supervisor.py     # Orchestration (router + research + writing)
│   ├── query_router.py   # Intent and routing
│   ├── research_team.py  # Retrieval
│   ├── writing_team.py   # Grounded generation
│   ├── generate_grounded.py
│   ├── retrieve.py
│   ├── rerank.py
│   ├── confidence.py
│   ├── ingest.py
│   ├── metadata.py
│   ├── feature_flags.py
│   └── prompts/
├── eval/
│   ├── run_ragas.py      # RAGAS evaluation
│   └── gates.py          # Quality gates
├── demos/
│   ├── enterprise_hallucination_prevention.py
│   ├── enterprise_confidence_risk.py
│   └── enterprise_audit_trail.py
├── mcp/
│   └── server.py
├── pages/
│   └── Documentation.py  # In-app documentation
├── data/                  # Sample or default documents
└── policies.yaml
```

---

## Configuration

Primary configuration is in `config.yaml` (LLM model and URL, retrieval and rerank settings, Qdrant collection, evaluation gates). Environment variables override where applicable; see `.env.example` for names and defaults.

Important knobs:

- **LLM:** `config.yaml` under `llm` (model, base_url, temperature, max_tokens).
- **Retrieval:** `top_k`, `use_rerank`, `context_limit`, etc.
- **Qdrant:** URL and collection name (config or env).
- **Evaluation:** Gate thresholds under `evaluation.gates` (e.g. faithfulness, context precision).

---

## API usage

**Engine (canonical entry)**

```python
from rag.engine import run_enterprise_query

result = run_enterprise_query(
    "Your question here",
    trace_id="optional-id",
    feature_flags=None,  # optional FeatureFlags for demos
)

# result keys: answer, claims, sources_used, decision_path, confidence,
# confidence_reason, documents, trace_id, refusal_reason (if refused), etc.
```

**Explain / audit**

```python
from rag.engine import run_enterprise_query
from rag.explain import explain_response

result = run_enterprise_query("Your question")
audit = explain_response(result)  # Same data, audit-oriented structure
```

---

## Evaluation

RAGAS-based evaluation (faithfulness, context precision, context recall, answer relevancy) and configurable quality gates:

```bash
python -m eval.run_ragas
python -m eval.gates
```

Gate thresholds are defined in `config.yaml` under `evaluation.gates`.

---

## Security and data handling

- Queries are processed per request; the system does not train on user input.
- With default setup (local Ollama, local or self-hosted Qdrant), data stays on your infrastructure.
- No telemetry or external API calls are required for core RAG; optional Cohere rerank uses their API if configured.
- Audit outputs (trace IDs, decision path, claims, sources) support compliance and internal review.

---

## License and contributing

This project is licensed under the MIT License; see [LICENSE](LICENSE) in the repository. Contributions should preserve refusal behavior, grounding guarantees, and auditability; changes that affect safety or compliance surface should be documented and reviewed.

---

## References

- Engine API: `rag/engine.py` (`run_enterprise_query`)
- Explain API: `rag/explain.py`
- Configuration: `config.yaml`, `.env.example`
- Evaluation: `eval/run_ragas.py`, `eval/gates.py`
- In-app docs: run `ui.py` and open the Documentation page.
