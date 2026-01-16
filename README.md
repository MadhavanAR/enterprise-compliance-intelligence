# RAG Platform Starter Kit

**Production-Grade RAG Architecture — 100% Local-First**

Same architecture as enterprise RAG systems, but runs entirely on your machine. No API keys required. No data leaves your environment.

---

## 🎯 Problem

Most RAG implementations are either:
- ❌ **Toy projects**: Basic embeddings + ChatGPT, no evaluation
- ❌ **Enterprise locked-in**: Proprietary APIs, data leaves your infrastructure
- ❌ **Boilerplate hell**: LangChain tutorials that don't scale to production

**This is different.**

This is a **complete, production-grade RAG platform** that:
- ✅ Runs 100% locally (privacy-first)
- ✅ Uses hybrid retrieval (dense + sparse)
- ✅ Implements multi-agent orchestration
- ✅ Includes proper evaluation (RAGAS)
- ✅ Has guardrails ("I don't know" instead of hallucination)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor (Router)                       │
│              Routes to appropriate team                      │
└──────┬─────────────────────────────────────────┬────────────┘
       │                                         │
       ▼                                         ▼
┌─────────────────────┐              ┌─────────────────────┐
│   Research Team     │              │   Writing Team      │
│                     │              │                     │
│  ┌──────────────┐   │              │  ┌──────────────┐   │
│  │ RAG Search   │   │              │  │ Note Taker   │   │
│  │ + MCP Tools  │   │              │  └──────┬───────┘   │
│  └──────┬───────┘   │              │         │           │
│         │           │              │         ▼           │
│         ▼           │              │  ┌──────────────┐   │
│  ┌──────────────┐   │              │  │Copy Editor   │   │
│  │  Context +   │   │              │  └──────┬───────┘   │
│  │ Research     │   │              │         │           │
│  │  Notes       │   │              │         ▼           │
│  └──────────────┘   │              │  ┌──────────────┐   │
└──────────┬──────────┘              │  │Dopeness Editor│  │
           │                         │  │  (LLM)       │   │
           └───────────┬─────────────┘  └──────┬───────┘   │
                       │                      │           │
                       ▼                      ▼           │
              ┌─────────────────────────────────────────┐ │
              │         Final Answer                    │ │
              │  (Ground-truth verified)                │◄┘
              └─────────────────────────────────────────┘
```

### Core Components

#### 1. **Hybrid Retrieval** (`rag/retrieve.py`)
- **Dense vectors**: Semantic search using SentenceTransformers
- **Sparse (BM25)**: Keyword matching for exact terms
- **Reranking**: Cohere API for second-stage filtering (optional)

#### 2. **Multi-Agent System** (`rag/supervisor.py`)
- **Supervisor**: Routing logic (no content generation)
- **Research Team**: RAG retrieval + MCP tools (web search, dice, etc.)
- **Writing Team**: Note-taking → Copy editing → Final answer generation

#### 3. **Evaluation** (`eval/run_ragas.py`)
- **RAGAS metrics**: Faithfulness, relevancy, precision, recall
- **Local judge LLM**: Ollama (no OpenAI dependency)
- **Git-based benchmarks**: Track improvements over time

#### 4. **Guardrails** (`rag/generate.py`)
- **Strict grounding**: Answers ONLY from context
- **Citation enforcement**: Every claim must cite [Doc 1], [Doc 2]
- **Safe defaults**: "I don't know" instead of hallucination

#### 5. **MCP Tools** (`mcp/server.py`)
- **Extensible**: Add custom tools (web search, calculators, APIs)
- **Agent-safe**: Tools only in Research Team (separation of concerns)

---

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Install Qdrant (vector database)
docker run -p 6333:6333 qdrant/qdrant

# 2. Install Ollama (local LLM)
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# 3. Pull the model
ollama pull llama3.2:latest

# 4. Start Ollama
ollama serve
```

### Installation

```bash
# Clone and install
git clone <your-repo>
cd rag-platform
pip install -r requirements.txt

# Optional: Set up Cohere for reranking (free tier available)
# export COHERE_API_KEY="your-key-here"
```

### Run Demos

```bash
# Demo 1: Internal docs Q&A
python -m rag.run

# Demo 2: Guardrail demo ("I don't know")
python demos/demo_guardrails.py

# Demo 3: Multi-agent research → writing
python demos/demo_multi_agent.py
```

### Web UI

```bash
streamlit run ui.py
```

---

## 🎬 Demos

### Demo 1: Internal Docs Q&A

Query your knowledge base with production-grade retrieval:

```bash
python -m rag.run
```

**What it does:**
- Ingest documents into Qdrant
- Hybrid search (dense + BM25)
- Optional reranking with Cohere
- Generate answer with local LLM

### Demo 2: Guardrails ("I don't know")

See how the system refuses to hallucinate:

```bash
python demos/demo_guardrails.py
```

**What it demonstrates:**
- Questions with context → proper answers
- Questions without context → "I don't know"
- Citation enforcement
- No hallucination

### Demo 3: Multi-Agent Workflow

Research Team → Writing Team pipeline:

```bash
python demos/demo_multi_agent.py
```

**What it shows:**
- Supervisor routing
- Research Team using RAG + MCP tools
- Writing Team generating structured answers
- Full traceability

---

## 📊 Why This Beats LangChain Boilerplate

| Feature | LangChain Tutorials | This Platform |
|---------|---------------------|---------------|
| **Retrieval** | Basic embeddings | Hybrid (dense + BM25) |
| **Orchestration** | Simple chains | Multi-agent (Supervisor → Teams) |
| **Evaluation** | None | RAGAS with local judge |
| **Guardrails** | Optional | Built-in (citations, "I don't know") |
| **Tools** | Basic examples | MCP integration ready |
| **Production** | ❌ | ✅ Eval, logging, config management |
| **Privacy** | OpenAI API | 100% local |

---

## 🔧 Configuration

Environment variables (`.env`):

```bash
# Required
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:latest

# Optional
COHERE_API_KEY=your-key  # For reranking
USE_RERANK=true
TOP_K=5
```

---

## 📈 Evaluation

### Precision/Recall (Retrieval Quality)

```bash
python -m eval.run_eval
```

**Output:**
```
NO_RERANK → Precision: 0.20, Recall: 0.33
RERANK    → Precision: 0.25, Recall: 0.50
```

### RAGAS Metrics (Answer Quality)

```bash
python -m eval.run_ragas
```

**Output:**
```
RAGAS RESULTS
{
  'answer_relevancy': 0.5377,
  'context_precision': 1.0000,
  'faithfulness': 1.0000,      # ← No hallucination!
  'context_recall': 1.0000
}
```

---

## 🎯 Use Cases

### 1. **Internal Knowledge Base**
- Employee handbook Q&A
- Technical documentation search
- Company policy lookup

### 2. **Client Projects**
- Legal document analysis
- Medical record querying
- Financial report understanding

### 3. **AI Consulting**
- Starter template for clients
- Workshop material
- Portfolio demonstration

### 4. **Privacy-Critical Applications**
- Healthcare (HIPAA compliance)
- Finance (regulatory requirements)
- Government (data sovereignty)

---

## 🧠 Technical Highlights

- **Hybrid Retrieval**: Best of both worlds (semantic + keyword)
- **Reranking**: Two-stage filtering for precision
- **Multi-Agent**: Separated concerns (research vs. writing)
- **MCP Tools**: Extensible tool system (web search, APIs, etc.)
- **Local-First**: No external API dependencies (except optional Cohere)
- **Evaluation**: RAGAS with local judge LLM
- **Guardrails**: Citation enforcement, "I don't know" fallback

---

## 📚 Project Structure

```
rag-platform/
├── rag/                  # Core RAG pipeline
│   ├── ingest.py        # Document loading & chunking
│   ├── retrieve.py      # Hybrid search + reranking
│   ├── generate.py      # Answer generation (with guardrails)
│   ├── supervisor.py    # Multi-agent orchestrator
│   ├── research_team.py # RAG + MCP tools
│   └── writing_team.py  # Note-taking → Answer generation
├── mcp/                 # Model Context Protocol tools
│   └── server.py        # roll_dice, web_search, etc.
├── eval/                # Evaluation framework
│   ├── run_eval.py      # Precision/recall
│   └── run_ragas.py     # RAGAS metrics
├── demos/               # Demo scripts
└── ui.py                # Streamlit web interface
```

---

## 🔐 Privacy & Security

### Data Handling

**NO TRAINING ON USER DATA**

This system does NOT train models on user data. All data processing is:
- ✅ **100% local execution** (no data leaves your machine)
- ✅ **No external APIs** (except optional Cohere reranking - data sent only if you enable it)
- ✅ **On-premise ready** (Qdrant, Ollama self-hosted)
- ✅ **No data retention** (queries are processed, not stored)
- ✅ **No telemetry** (zero tracking, zero analytics)

### Data Flow Diagram

```
User Query
    │
    ├─► Local Processing Only
    │   │
    │   ├─► Qdrant (Local Vector DB)
    │   │   └─► Embeddings stored locally
    │   │
    │   ├─► Ollama (Local LLM)
    │   │   └─► Model runs on your machine
    │   │
    │   └─► Generated Answer
    │       └─► Returned to user (not stored)
    │
    └─► Optional: Cohere Reranking
        └─► Only if COHERE_API_KEY is set
            └─► Query + docs sent to Cohere API
                └─► Reranked results returned
```

**What data leaves your system:**
- ❌ **Never**: User queries, document content, embeddings (unless you enable Cohere)
- ⚠️ **Optional**: Query + context sent to Cohere API (only if `COHERE_API_KEY` is set)

### Security Best Practices

- ✅ **No secrets in code** (all API keys in `.env`, see `.env.example`)
- ✅ **Config-driven** (no hardcoded values in production code)
- ✅ **Structured logging** (trace IDs for audit trails)
- ✅ **Deterministic execution** (temperature=0, no randomness in production)
- ✅ **Evaluation gates** (quality checks before deployment)

### Compliance Signals

This platform is designed for:
- **HIPAA compliance** (healthcare - all data stays local)
- **SOC 2 readiness** (audit trails via structured logs)
- **GDPR compliance** (data sovereignty, no external processing)
- **Regulatory environments** (finance, government)

### Configuration Files

- `.env.example` - Template for environment variables (no secrets)
- `config.yaml` - All runtime configuration (no API keys)
- `requirements.txt` - Dependency tracking

**Security-conscious by default.**

---

## 🚦 Status

**Production-Ready** ✅

- Hybrid retrieval implemented
- Multi-agent system functional
- Evaluation framework working
- Guardrails enforced
- MCP tools integrated

**Next Steps (if needed):**
- Add more MCP tools (Tavily, custom APIs)
- Expand evaluation dataset
- Deploy UI for end users

---

## 📄 License

[Your License Here]

---

## 🤝 Contributing

This is a **starter kit** — fork it, customize it, make it your own.

**Ideas for contributions:**
- Additional MCP tools
- More evaluation metrics
- UI improvements
- Documentation examples

---

## 💡 Why This Exists

Most RAG tutorials stop at "embed some text and call ChatGPT."

**This platform demonstrates:**
- How to build **production-grade** RAG systems
- How to **evaluate** RAG quality objectively
- How to **prevent hallucination** with guardrails
- How to **scale** with multi-agent architecture
- How to stay **privacy-compliant** with local-first design

**Built for:**
- Startups building AI features
- Consultants delivering RAG projects
- Dev teams wanting a complete reference
- Founders who need enterprise-grade RAG without enterprise lock-in

---

**Same architecture as enterprise RAG — but runs 100% locally.**
