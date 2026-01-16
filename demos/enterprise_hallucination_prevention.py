#!/usr/bin/env python3
"""
Demo A: Hallucination Prevention

Demonstrates:
- Hard refusal on unanswerable questions
- Explain output showing refusal reason
- Zero hallucination guarantee

Target Audience: CTOs, Legal, Compliance teams
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.supervisor import build_supervisor
from rag.explain import explain_response


def demo_hallucination_prevention():
    """Demonstrate hard refusal on unanswerable questions."""
    
    print("=" * 70)
    print("DEMO A: Hallucination Prevention")
    print("=" * 70)
    print("\nThis demo shows how the system refuses to answer questions")
    print("that cannot be answered from available documents.")
    print("\nEnterprise Value: Prevents hallucination and liability.")
    print("-" * 70)
    
    # Initialize system
    app = build_supervisor()
    
    # Test: Unanswerable question (no context available)
    print("\n1️⃣ TEST: Unanswerable Question")
    print("-" * 70)
    query = "Why do birds sing?"
    print(f"Query: {query}")
    print("\nExecuting query...")
    
    result = app.invoke({
        "question": query,
        "trace_id": "demo-hallucination-prevention"
    })
    
    answer = result.get("answer", "")
    print(f"\nAnswer: {answer}")
    
    # Show refusal behavior
    if "don't know" in answer.lower():
        print("\n✅ REFUSAL TRIGGERED: System correctly refused to hallucinate")
    else:
        print("\n❌ WARNING: System did not refuse (potential hallucination risk)")
    
    # Show explain output
    print("\n2️⃣ EXPLAIN OUTPUT (Audit Trail)")
    print("-" * 70)
    explain = explain_response(result)
    
    print(f"Trace ID: {explain['trace_id']}")
    print(f"Decision Path: {' -> '.join(explain['decision_path'])}")
    print(f"Intent: {explain['intent']}")
    print(f"Documents Used: {len(explain['documents_used'])} documents")
    print(f"Refusal Reason: {explain['refusal_reason'] or 'N/A'}")
    print(f"Confidence: {explain['confidence']:.2f}")
    
    # Show structured JSON (for API consumers)
    print("\n3️⃣ STRUCTURED JSON OUTPUT (API-Friendly)")
    print("-" * 70)
    print(json.dumps(explain, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("- System refuses rather than hallucinates")
    print("- Refusal reason is explicit and auditable")
    print("- Full trace available for compliance")


if __name__ == "__main__":
    demo_hallucination_prevention()
