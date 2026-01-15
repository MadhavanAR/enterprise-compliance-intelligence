from rag.writing_team import build_writing_graph

app = build_writing_graph()

result = app.invoke({
    "research_notes": [
        "BM25 is a sparse keyword-based retrieval algorithm",
        "It complements dense vector search in RAG"
    ]
})

print(result["final_post"])
