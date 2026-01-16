# Demo Guide

Quick reference for running the three product demos.

---

## Demo 1: Internal Docs Q&A

**Purpose**: Show production-grade retrieval and answer generation

```bash
python main.py
```

**What it demonstrates:**
- Document ingestion into Qdrant
- Hybrid search (dense + BM25)
- Optional reranking with Cohere
- Answer generation with local LLM

---

## Demo 2: Guardrails ("I don't know")

**Purpose**: Demonstrate hallucination prevention

```bash
python demos/demo_guardrails.py
```

**What it shows:**
- Questions WITH context → proper answers with citations
- Questions WITHOUT context → "I don't know" (no hallucination)
- Citation enforcement
- Enterprise-safe behavior

---

## Demo 3: Multi-Agent Workflow

**Purpose**: Show Supervisor → Research Team → Writing Team pipeline

```bash
python demos/demo_multi_agent.py
```

**What it demonstrates:**
- Supervisor routing logic
- Research Team using RAG + MCP tools
- Writing Team generating structured answers
- Full traceability (research notes → final answer)

---

## All Demos Together

Run all three demos in sequence:

```bash
# Demo 1: Internal docs
python main.py

# Demo 2: Guardrails
python demos/demo_guardrails.py

# Demo 3: Multi-agent
python demos/demo_multi_agent.py
```

---

## Web UI

For interactive exploration:

```bash
streamlit run ui.py
```

Opens a browser-based interface for querying the RAG system.

---

## Evaluation Demos

### Precision/Recall (Retrieval Quality)

```bash
python -m eval.run_eval
```

Shows how reranking improves precision and recall.

### RAGAS Metrics (Answer Quality)

```bash
python -m eval.run_ragas
```

Shows faithfulness, relevancy, precision, and recall scores.
