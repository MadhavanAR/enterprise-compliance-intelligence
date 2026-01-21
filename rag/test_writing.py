from rag.engine import run_enterprise_query

result = run_enterprise_query("Explain BM25 keyword search in RAG systems")
print(result["answer"])
