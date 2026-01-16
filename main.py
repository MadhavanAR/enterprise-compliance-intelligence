#!/usr/bin/env python3
"""
Demo 1: Internal Docs Q&A

Demonstrates:
- Document ingestion into Qdrant
- Hybrid search (dense + BM25)
- Optional reranking with Cohere
- Answer generation with local LLM
"""

from dotenv import load_dotenv
load_dotenv()

from rag.supervisor import build_supervisor

def demo_internal_docs():
    """Demonstrate internal documentation Q&A."""
    app = build_supervisor()
    
    print("=" * 70)
    print("DEMO 1: INTERNAL DOCS Q&A")
    print("=" * 70)
    print()
    print("Query your knowledge base with production-grade retrieval.")
    print()
    print("-" * 70)
    
    # Example query about BM25
    question = "Explain BM25 keyword search in RAG systems"
    print(f"Question: {question}")
    print()
    
    result = app.invoke({"question": question})
    
    print("Answer:")
    print("-" * 70)
    print(result.get("answer", ""))
    print()
    print("-" * 70)
    print()
    print(f"📊 Context used: {len(result.get('research_notes', []))} documents")
    print(f"🔧 Tools called: {len(result.get('tool_calls', []))}")
    if result.get('tool_calls'):
        for tool_call in result.get('tool_calls', []):
            print(f"   • {tool_call.get('tool', 'unknown')}")
    print()
    print("✅ Demo complete!")

if __name__ == "__main__":
    demo_internal_docs()
