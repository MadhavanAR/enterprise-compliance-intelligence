class RagasEmbeddingAdapter:
    """
    Adapter to make SentenceTransformer model compatible with RAGAS embeddings interface.
    Works with the model from rag.embeddings module.
    """
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        """Embed a list of documents using SentenceTransformer."""
        if isinstance(texts, str):
            texts = [texts]
        # SentenceTransformer.encode returns numpy array, convert to list
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings

    def embed_query(self, text):
        """Embed a single query text."""
        return self.embed_documents([text])[0]