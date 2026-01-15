from rag.graph import app

result = app.invoke(
    {"question": "Explain BM25 keyword search in RAG systems"}
)

print("\nFINAL ANSWER\n")
print(result["answer"])