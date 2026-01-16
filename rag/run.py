from dotenv import load_dotenv
from rag.supervisor import build_supervisor

load_dotenv()

app = build_supervisor()

result = app.invoke({
    # "question": "Explain BM25 keyword search in RAG systems"
    # "question": "Why do birds sing?"
    "question": "What did Da Vinci say about solitude?"
})

print("\nFINAL ANSWER\n")
print(result["answer"])
