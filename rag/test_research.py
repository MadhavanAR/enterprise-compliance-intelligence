from rag.engine import run_enterprise_query

result = run_enterprise_query("What is BM25 in RAG systems?")
print(result["answer"])
