from dotenv import load_dotenv
from rag.engine import run_enterprise_query

load_dotenv()

result = run_enterprise_query(
    # "Explain BM25 keyword search in RAG systems"
    # "What compliance certifications does AWS have?"
    # "Should AWS be trusted with sensitive data?"
    "What did AWS say about quantum ethics?"
    # "Why do birds sing?"
    # "What did Da Vinci say about solitude?"
)

print("\nFINAL ANSWER\n")
print(result.get("answer", ""))
