import json
from rag.retrieve import search

def precision_recall(retrieved, relevant):
    """
    Substring-based relevance:
    A retrieved doc is relevant if it CONTAINS
    any of the expected relevant phrases.
    """
    hits = 0

    for doc in retrieved:
        if any(rel.lower() in doc.lower() for rel in relevant):
            hits += 1

    precision = hits / len(retrieved) if retrieved else 0
    recall = hits / len(relevant) if relevant else 0

    return precision, recall

with open("eval/benchmarks.json") as f:
    benchmarks = json.load(f)

modes = {
    "no_rerank": False,
    "rerank": True,
}

results = {}

for mode, flag in modes.items():
    total_p, total_r = 0, 0

    for b in benchmarks:
        docs = search(b["query"], use_rerank=flag)
        p, r = precision_recall(docs, b["relevant_docs"])
        total_p += p
        total_r += r

    n = len(benchmarks)
    results[mode] = {
        "precision": total_p / n,
        "recall": total_r / n,
    }

print("\nEVAL RESULTS")
for k, v in results.items():
    print(f"{k.upper()} → Precision: {v['precision']:.2f}, Recall: {v['recall']:.2f}")