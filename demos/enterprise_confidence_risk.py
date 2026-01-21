#!/usr/bin/env python3
"""
Demo B: Confidence & Risk Assessment

Demonstrates:
- Different confidence scores for same question
- Risk level transparency
- Factors affecting confidence

Target Audience: Risk management, Compliance teams
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.engine import run_enterprise_query
from rag.explain import explain_response


def demo_confidence_risk():
    """Demonstrate confidence scoring and risk assessment."""
    
    print("=" * 70)
    print("DEMO B: Confidence & Risk Assessment")
    print("=" * 70)
    print("\nThis demo shows how confidence scores reflect answer quality")
    print("and risk factors. Lower confidence = higher risk.")
    print("\nEnterprise Value: Transparent risk assessment for decision-makers.")
    print("-" * 70)
    
    # Test 1: Question with good context (should have higher confidence)
    print("\n1️⃣ TEST 1: Question with Good Context")
    print("-" * 70)
    query = "Explain BM25 keyword search in RAG systems"
    print(f"Query: {query}")
    print("\nExecuting query...")
    
    result1 = run_enterprise_query(query, trace_id="demo-confidence-1")
    
    explain1 = explain_response(result1)
    
    print(f"\nAnswer: {explain1['answer'][:100]}...")
    print(f"Confidence: {explain1['confidence']:.2f}")
    print(f"Confidence Reason: {explain1['confidence_reason'][:100]}...")
    print(f"Claims: {len(explain1['claims'])}")
    print(f"Sources: {explain1['sources_used']}")
    
    # Test 2: Question with metadata filter (should affect confidence)
    print("\n2️⃣ TEST 2: Question with Metadata Filter (No Match)")
    print("-" * 70)
    query2 = "What did Da Vinci say about solitude?"
    print(f"Query: {query2}")
    print(f"Metadata Filter: author=Da Vinci")
    print("\nExecuting query...")
    
    result2 = run_enterprise_query(
        query2,
        metadata_filters={"author": "Da Vinci"},
        trace_id="demo-confidence-2",
    )
    
    explain2 = explain_response(result2)
    
    print(f"\nAnswer: {explain2['answer']}")
    print(f"Confidence: {explain2['confidence']:.2f}")
    print(f"Refusal Reason: {explain2['refusal_reason'] or 'N/A'}")
    print(f"Documents Used: {len(explain2['documents_used'])}")
    
    # Compare confidence scores
    print("\n3️⃣ CONFIDENCE COMPARISON")
    print("-" * 70)
    print(f"Test 1 (Good Context): {explain1['confidence']:.2f}")
    print(f"Test 2 (No Match): {explain2['confidence']:.2f}")
    print(f"\nConfidence Difference: {explain1['confidence'] - explain2['confidence']:.2f}")
    
    if explain1['confidence'] > explain2['confidence']:
        print("\n✅ System correctly assigns higher confidence to well-supported answers")
    
    # Risk interpretation
    print("\n4️⃣ RISK INTERPRETATION")
    print("-" * 70)
    print("Confidence Levels:")
    print("- 0.8 - 1.0: High confidence (low risk)")
    print("- 0.5 - 0.8: Medium confidence (moderate risk)")
    print("- 0.0 - 0.5: Low confidence (high risk)")
    
    risk_level1 = "LOW" if explain1['confidence'] >= 0.8 else "MODERATE" if explain1['confidence'] >= 0.5 else "HIGH"
    risk_level2 = "LOW" if explain2['confidence'] >= 0.8 else "MODERATE" if explain2['confidence'] >= 0.5 else "HIGH"
    
    print(f"\nTest 1 Risk Level: {risk_level1} (confidence: {explain1['confidence']:.2f})")
    print(f"Test 2 Risk Level: {risk_level2} (confidence: {explain2['confidence']:.2f})")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("- Confidence scores reflect answer quality and risk")
    print("- Metadata mismatches reduce confidence")
    print("- Decision-makers can set confidence thresholds")


if __name__ == "__main__":
    demo_confidence_risk()
