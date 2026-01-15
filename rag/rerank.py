# Document reranking module
import os
import cohere

co = cohere.Client(os.environ["COHERE_API_KEY"])

def rerank(query: str, docs: list[str], top_k: int = 5):
    res = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=docs,
        top_n=top_k,
    )
    return [docs[r.index] for r in res.results]