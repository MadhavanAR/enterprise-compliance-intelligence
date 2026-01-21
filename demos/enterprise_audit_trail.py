#!/usr/bin/env python3
"""
Demo C: Complete Audit Trail

Demonstrates:
- Full traceability from query to answer
- Claims → sources mapping
- Compliance-ready audit trail

Target Audience: Compliance, Legal, Audit teams
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.engine import run_enterprise_query
from rag.explain import explain_response


def demo_audit_trail():
    """Demonstrate complete audit trail for compliance."""
    
    print("=" * 70)
    print("DEMO C: Complete Audit Trail")
    print("=" * 70)
    print("\nThis demo shows the complete audit trail from query to answer,")
    print("demonstrating full traceability for compliance purposes.")
    print("\nEnterprise Value: Regulatory compliance, legal protection.")
    print("-" * 70)
    
    # Execute a normal query
    print("\n1️⃣ EXECUTING QUERY")
    print("-" * 70)
    query = "Explain BM25 keyword search in RAG systems"
    print(f"Query: {query}")
    print("\nExecuting query...")
    
    result = run_enterprise_query(query, trace_id="demo-audit-trail")
    
    trace_id = result.get("trace_id")
    print(f"\nTrace ID: {trace_id}")
    print("(This ID can be used to retrieve the full audit trail later)")
    
    # Generate explain output
    print("\n2️⃣ GENERATING AUDIT TRAIL")
    print("-" * 70)
    explain = explain_response(result)
    
    print(f"Trace ID: {explain['trace_id']}")
    print(f"Original Query: {explain['original_query']}")
    print(f"Decision Path: {' -> '.join(explain['decision_path'])}")
    print(f"Intent: {explain['intent']}")
    print(f"Tools Used: {explain['tools_used'] or 'None'}")
    print(f"Metadata Filters: {explain['metadata_filters'] or 'None'}")
    
    # Show documents used
    print("\n3️⃣ DOCUMENTS USED")
    print("-" * 70)
    print(f"Total Documents: {len(explain['documents_used'])}")
    for i, doc in enumerate(explain['documents_used'][:3], 1):  # Show first 3
        preview = doc[:150] + "..." if len(doc) > 150 else doc
        print(f"\n  Document {i}: {preview}")
    
    # Show claims → sources mapping
    print("\n4️⃣ CLAIMS → SOURCES MAPPING")
    print("-" * 70)
    print(f"Total Claims: {len(explain['claims'])}")
    print(f"Sources Referenced: {explain['sources_used']}")
    
    for i, claim in enumerate(explain['claims'][:5], 1):  # Show first 5
        claim_text = claim.get('text', '')[:80] + "..." if len(claim.get('text', '')) > 80 else claim.get('text', '')
        source_doc = claim.get('source_doc', 'Unknown')
        print(f"\n  Claim {i}: {claim_text}")
        print(f"    Source: {source_doc}")
    
    # Show answer with confidence
    print("\n5️⃣ ANSWER & CONFIDENCE")
    print("-" * 70)
    print(f"Answer: {explain['answer'][:200]}...")
    print(f"Confidence: {explain['confidence']:.2f}")
    print(f"Confidence Reason: {explain['confidence_reason'][:150]}...")
    
    # Show refusal status
    if explain['refusal_reason']:
        print(f"\nRefusal Reason: {explain['refusal_reason']}")
    
    # Complete audit trail JSON
    print("\n6️⃣ COMPLETE AUDIT TRAIL (JSON)")
    print("-" * 70)
    print("This is the format that would be stored for compliance:")
    print(json.dumps(explain, indent=2))
    
    # Compliance checklist
    print("\n7️⃣ COMPLIANCE CHECKLIST")
    print("-" * 70)
    checks = {
        "Trace ID Present": bool(explain['trace_id']),
        "Original Query Recorded": bool(explain['original_query']),
        "Decision Path Tracked": len(explain['decision_path']) > 0,
        "Claims Mapped to Sources": len(explain['claims']) > 0 and all(c.get('source_doc') for c in explain['claims']),
        "Confidence Score Provided": explain['confidence'] is not None,
        "Documents Used Recorded": len(explain['documents_used']) > 0,
        "Refusal Reason Documented": explain['refusal_reason'] is not None or explain['answer'] != "I don't know."
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    all_passed = all(checks.values())
    if all_passed:
        print("\n✅ ALL COMPLIANCE CHECKS PASSED")
    else:
        print("\n⚠️ SOME COMPLIANCE CHECKS FAILED")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("- Every answer is fully traceable via trace_id")
    print("- Claims map directly to source documents")
    print("- Complete audit trail available for regulatory compliance")


if __name__ == "__main__":
    demo_audit_trail()
