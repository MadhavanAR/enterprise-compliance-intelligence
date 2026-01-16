from datasets import Dataset

def build_dataset():
    return Dataset.from_dict({
        "question": [
            "Explain BM25 keyword search in RAG systems"
        ],
        "answer": [
            "BM25 is a sparse keyword-based retrieval algorithm used in hybrid RAG systems to ensure exact keyword matching alongside dense semantic search."
        ],
        "contexts": [[
            "Hybrid retrieval combines dense vector search with sparse keyword-based search such as BM25. Dense search captures semantic meaning, while sparse search ensures exact keyword matches."
        ]],
        "ground_truth": [
            "BM25 is a keyword-based retrieval algorithm used in hybrid RAG systems."
        ]
    })