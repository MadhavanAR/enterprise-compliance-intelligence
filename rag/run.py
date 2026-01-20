from dotenv import load_dotenv
from rag.supervisor import build_supervisor

load_dotenv()

app = build_supervisor()

result = app.invoke({
    # "question": "Explain BM25 keyword search in RAG systems"
    # "question": "What compliance certifications does AWS have?"
    # "question": "Should AWS be trusted with sensitive data?"
    "question": "What did AWS say about quantum ethics?"
    # "question": "Why do birds sing?"
    # "question": "What did Da Vinci say about solitude?"
})

print("\nFINAL ANSWER\n")
print(result["answer"])
