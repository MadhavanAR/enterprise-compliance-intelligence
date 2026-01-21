#!/usr/bin/env python3
"""
Demo 3: Multi-Agent Workflow (Research Team → Writing Team)

Demonstrates:
- Supervisor routing
- Research Team using RAG + MCP tools
- Writing Team generating structured answers
- Full traceability
"""

from dotenv import load_dotenv
load_dotenv()

from rag.engine import run_enterprise_query

def demo_multi_agent():
    """Demonstrate multi-agent workflow."""
    print("=" * 70)
    print("DEMO 3: MULTI-AGENT WORKFLOW")
    print("=" * 70)
    print()
    print("Architecture: Supervisor → Research Team → Writing Team")
    print()
    
    # Demo 1: RAG-only query (uses Research Team RAG pipeline)
    print("📊 Demo 1: RAG-Only Query (Research Team → Writing Team)")
    print("-" * 70)
    print("Question: Explain BM25 keyword search in RAG systems")
    print()
    
    result1 = run_enterprise_query("Explain BM25 keyword search in RAG systems")
    
    print("🔬 Research Team Output:")
    print(f"   • Documents retrieved: {len(result1.get('documents', []) or [])}")
    print()
    
    print("✍️  Writing Team Output:")
    print(f"   • Answer generated: {len(result1.get('answer', ''))} characters")
    print(f"   • Preview: {result1.get('answer', '')[:150]}...")
    print()
    print()
    
    # Demo 2: MCP tool query (uses Research Team MCP tools)
    print("📊 Demo 2: MCP Tool Query (Research Team → Writing Team)")
    print("-" * 70)
    print("Question: Can you roll the damage for a fourth-level fireball?")
    print()
    
    result2 = run_enterprise_query("Can you roll the damage for a fourth-level fireball?")
    
    print("🔬 Research Team Output:")
    print(f"   • Documents retrieved: {len(result2.get('documents', []) or [])}")
    print()
    
    print("✍️  Writing Team Output:")
    print(f"   • Answer generated: {len(result2.get('answer', ''))} characters")
    print(f"   • Preview: {result2.get('answer', '')[:150]}...")
    print()
    print()
    
    # Demo 3: Web search query (if MCP web_search works)
    print("📊 Demo 3: Web Search Query (Research Team → Writing Team)")
    print("-" * 70)
    print("Question: Did the Edmonton Oilers win the 2025 Stanley Cup?")
    print()
    
    result3 = run_enterprise_query("Did the Edmonton Oilers win the 2025 Stanley Cup?")
    
    print("🔬 Research Team Output:")
    print(f"   • Documents retrieved: {len(result3.get('documents', []) or [])}")
    print()
    
    print("✍️  Writing Team Output:")
    print(f"   • Answer generated: {len(result3.get('answer', ''))} characters")
    print(f"   • Preview: {result3.get('answer', '')[:150]}...")
    print()
    
    print("=" * 70)
    print("✅ Multi-agent demo complete!")
    print("=" * 70)
    print()
    print("Key takeaways:")
    print("  • Supervisor routes intelligently (no content generation)")
    print("  • Research Team handles retrieval + tools")
    print("  • Writing Team generates structured answers")
    print("  • Full traceability (research notes → final answer)")
    print("  • Separation of concerns (agents do one thing well)")

if __name__ == "__main__":
    demo_multi_agent()
