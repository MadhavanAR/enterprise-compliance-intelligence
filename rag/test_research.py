from rag.research_team import build_research_graph

app = build_research_graph()

result = app.invoke({
    "question": "What is BM25 in RAG systems?"
})

print(result["research_notes"])
