from ragas import evaluate
from ragas.llms import llm_factory
from ragas.embeddings import HuggingFaceEmbeddings
from openai import OpenAI
from eval.ragas_data import build_dataset

# Use Ollama as the RAGAS judge LLM via llm_factory
# Ollama exposes OpenAI-compatible API
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama doesn't require a real API key
)

judge_llm = llm_factory(
    "llama3.2:latest",
    client=ollama_client
)

# Use HuggingFace embeddings (local, no API key needed)
embeddings = HuggingFaceEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")

dataset = build_dataset()

# Pass llm and embeddings directly to evaluate (uses default metrics)
results = evaluate(
    dataset,
    llm=judge_llm,
    embeddings=embeddings
)

print("\nRAGAS RESULTS")
print(results)