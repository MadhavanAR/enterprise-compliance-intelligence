from datasets import Dataset
from rag.generate import generate_answer

def build_dataset():
    # Generate answer using improved prompt for better faithfulness
    question = "Explain BM25 keyword search in RAG systems"
    contexts = [
        "Hybrid retrieval combines dense vector search with sparse keyword-based search such as BM25. Dense search captures semantic meaning, while sparse search ensures exact keyword matches."
    ]
    
    # Generate answer with improved prompt (strict grounding + citations)
    answer = generate_answer(question, contexts)
    
    return Dataset.from_dict({
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [
            "BM25 is a keyword-based retrieval algorithm used in hybrid RAG systems."
        ]
    })