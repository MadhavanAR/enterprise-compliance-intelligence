#!/usr/bin/env python3
"""
Demo 2: Guardrails ("I don't know" instead of hallucination)

Demonstrates:
- Proper answers when context exists
- "I don't know" when context is missing
- Citation enforcement
- No hallucination
"""

from dotenv import load_dotenv
load_dotenv()

from rag.engine import run_enterprise_query

def demo_guardrails():
    """Demonstrate guardrails in action."""
    print("=" * 70)
    print("DEMO 2: GUARDRAILS - \"I don't know\" instead of hallucination")
    print("=" * 70)
    print()
    
    # Test 1: Question WITH context (should answer)
    print("📚 Test 1: Question WITH context")
    print("-" * 70)
    print("Question: Explain BM25 keyword search in RAG systems")
    print()
    
    result1 = run_enterprise_query("Explain BM25 keyword search in RAG systems")
    
    print("✅ Answer:", result1.get("answer", "")[:200])
    print()
    
    # Check if answer has citations
    has_citations = "Doc " in " ".join(result1.get("sources_used", []) or [])
    print(f"✓ Citations: {'YES' if has_citations else 'NO'}")
    print(f"✓ Documents used: {len(result1.get('documents', []) or [])} documents")
    print()
    print()
    
    # Test 2: Question WITHOUT context (should say "I don't know")
    print("📚 Test 2: Question WITHOUT context")
    print("-" * 70)
    print("Question: What is the capital of Mars?")
    print()
    
    result2 = run_enterprise_query("What is the capital of Mars?")
    
    answer2 = result2.get("answer", "")
    print(f"✅ Answer: {answer2[:200]}")
    print()
    
    # Check guardrail behavior
    says_dont_know = "don't know" in answer2.lower() or "i don't know" in answer2.lower()
    has_hallucination = any(word in answer2.lower() for word in ["capital", "mars", "city"])
    
    if says_dont_know:
        print("✓ Guardrail WORKING: System says 'I don't know'")
        print("✓ No hallucination: System refused to make up an answer")
    elif has_hallucination:
        print("⚠️  Guardrail FAILED: System hallucinated an answer")
    else:
        print("? Unexpected response")
    
    print()
    print()
    
    # Test 3: Partial context (should use what's available)
    print("📚 Test 3: Partial context (related but not exact match)")
    print("-" * 70)
    print("Question: What is hybrid retrieval?")
    print()
    
    result3 = run_enterprise_query("What is hybrid retrieval?")
    
    print("✅ Answer:", result3.get("answer", "")[:200])
    print()
    
    has_context = len(result3.get("documents", []) or []) > 0
    print(f"✓ Context found: {'YES' if has_context else 'NO'}")
    print()
    
    print("=" * 70)
    print("✅ Guardrails demo complete!")
    print("=" * 70)
    print()
    print("Key takeaways:")
    print("  • System answers when context exists")
    print("  • System says 'I don't know' when context is missing")
    print("  • Citations enforce grounding")
    print("  • No hallucination → Enterprise-safe behavior")

if __name__ == "__main__":
    demo_guardrails()
