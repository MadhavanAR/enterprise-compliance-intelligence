from ragas import evaluate
from ragas.llms import llm_factory
from openai import OpenAI

from eval.ragas_data import build_dataset
from eval.embeddings_adapter import RagasEmbeddingAdapter
from rag.embeddings import model  # Import the SentenceTransformer model


# Ollama judge LLM (OpenAI-compatible)
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

judge_llm = llm_factory(
    "llama3.2:latest",
    client=ollama_client
)

# Wrap your existing embeddings model for RAGAS
ragas_embeddings = RagasEmbeddingAdapter(model)

dataset = build_dataset()

results = evaluate(
    dataset,
    llm=judge_llm,
    embeddings=ragas_embeddings
)

print("\nRAGAS RESULTS")
print(results)