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

from rag.supervisor import build_supervisor
from rag.logger import logger

def demo_multi_agent():
    """Demonstrate multi-agent workflow."""
    app = build_supervisor()
    
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
    
    result1 = app.invoke({
        "question": "Explain BM25 keyword search in RAG systems"
    })
    
    print("🔬 Research Team Output:")
    print(f"   • Documents retrieved: {len(result1.get('research_notes', []))}")
    print(f"   • Tool calls: {len(result1.get('tool_calls', []))}")
    if result1.get('tool_calls'):
        for tool_call in result1.get('tool_calls', []):
            print(f"     - {tool_call.get('tool', 'unknown')}: {tool_call}")
    else:
        print("     - RAG retrieval only (no MCP tools)")
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
    
    result2 = app.invoke({
        "question": "Can you roll the damage for a fourth-level fireball?"
    })
    
    print("🔬 Research Team Output:")
    print(f"   • Documents retrieved: {len(result2.get('research_notes', []))}")
    print(f"   • Tool calls: {len(result2.get('tool_calls', []))}")
    if result2.get('tool_calls'):
        for tool_call in result2.get('tool_calls', []):
            tool_name = tool_call.get('tool', 'unknown')
            print(f"     - Tool: {tool_name}")
            if tool_name == 'roll_dice':
                print(f"       Sides: {tool_call.get('sides', 'N/A')}")
                print(f"       Count: {tool_call.get('count', 'N/A')}")
            elif tool_name == 'web_search':
                print(f"       Query: {tool_call.get('query', 'N/A')}")
    else:
        print("     - No MCP tools called (fallback to RAG)")
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
    
    result3 = app.invoke({
        "question": "Did the Edmonton Oilers win the 2025 Stanley Cup?"
    })
    
    print("🔬 Research Team Output:")
    print(f"   • Documents retrieved: {len(result3.get('research_notes', []))}")
    print(f"   • Tool calls: {len(result3.get('tool_calls', []))}")
    if result3.get('tool_calls'):
        for tool_call in result3.get('tool_calls', []):
            tool_name = tool_call.get('tool', 'unknown')
            print(f"     - Tool: {tool_name}")
            if tool_name == 'web_search':
                print(f"       Query: {tool_call.get('query', 'N/A')}")
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
