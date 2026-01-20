import os
import cohere

def _get_client():
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return None
    return cohere.Client(api_key)

def rerank_indices(query, docs, top_k=5):
    """
    Return indices of the best documents (preserves metadata mapping).
    Falls back deterministically when Cohere is not configured.
    """
    client = _get_client()
    if not docs:
        return []
    if client is None:
        return list(range(min(top_k, len(docs))))

    response = client.rerank(
        query=query,
        documents=docs,
        top_n=min(top_k, len(docs)),
        model="rerank-english-v3.0",
    )
    return [r.index for r in response.results]

def rerank(query, docs, top_k=5):
    client = _get_client()

    # 🔁 Graceful fallback
    if client is None:
        return docs[:top_k]

    response = client.rerank(
        query=query,
        documents=docs,
        top_n=top_k,
        model="rerank-english-v3.0",
    )

    return [docs[r.index] for r in response.results]