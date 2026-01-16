#!/usr/bin/env python3
"""
Evaluation Gates (FAANG-grade quality control)
Blocks releases if quality thresholds are not met
"""
import sys
from typing import Dict
from rag.config import (
    EVAL_FAITHFULNESS_MIN,
    EVAL_FAITHFULNESS_BLOCK,
    EVAL_PRECISION_MIN
)

def check_evaluation_gates(results: Dict[str, float]) -> tuple[bool, list[str]]:
    """
    Check if evaluation results meet quality gates.
    
    Returns:
        (passed: bool, warnings: list[str])
    """
    warnings = []
    blocked = False
    
    # Gate 1: Faithfulness (blocking)
    faithfulness = results.get("faithfulness", 0.0)
    if faithfulness < EVAL_FAITHFULNESS_MIN:
        msg = f"Faithfulness {faithfulness:.2f} < {EVAL_FAITHFULNESS_MIN} (BLOCKING)"
        if EVAL_FAITHFULNESS_BLOCK:
            blocked = True
            warnings.append(f"🚫 BLOCKED: {msg}")
        else:
            warnings.append(f"⚠️  WARNING: {msg}")
    
    # Gate 2: Context Precision (warning only by default)
    precision = results.get("context_precision", 0.0)
    if precision < EVAL_PRECISION_MIN:
        warnings.append(f"⚠️  WARNING: Context precision {precision:.2f} < {EVAL_PRECISION_MIN}")
    
    # Gate 3: Context Recall
    recall = results.get("context_recall", 0.0)
    recall_min = 0.8
    if recall < recall_min:
        warnings.append(f"⚠️  WARNING: Context recall {recall:.2f} < {recall_min}")
    
    passed = not blocked
    
    return passed, warnings

def main():
    """Run evaluation and check gates."""
    from eval.run_ragas import build_dataset
    from ragas import evaluate
    from ragas.llms import llm_factory
    from ragas.embeddings import HuggingFaceEmbeddings
    from openai import OpenAI
    from eval.embeddings_adapter import RagasEmbeddingAdapter
    from rag.embeddings import model
    
    print("=" * 70)
    print("EVALUATION GATES - Quality Control")
    print("=" * 70)
    print()
    
    # Setup (same as run_ragas.py)
    ollama_client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )
    
    judge_llm = llm_factory(
        "llama3.2:latest",
        client=ollama_client
    )
    
    ragas_embeddings = RagasEmbeddingAdapter(model)
    dataset = build_dataset()
    
    # Run evaluation
    print("Running RAGAS evaluation...")
    results = evaluate(
        dataset,
        llm=judge_llm,
        embeddings=ragas_embeddings
    )
    
    # Convert to dict
    results_dict = {
        "faithfulness": results.get("faithfulness", 0.0),
        "context_precision": results.get("context_precision", 0.0),
        "context_recall": results.get("context_recall", 0.0),
        "answer_relevancy": results.get("answer_relevancy", 0.0),
    }
    
    print("\nRAGAS RESULTS:")
    for metric, value in results_dict.items():
        print(f"  {metric}: {value:.4f}")
    
    print()
    print("=" * 70)
    print("CHECKING QUALITY GATES")
    print("=" * 70)
    
    passed, warnings = check_evaluation_gates(results_dict)
    
    for warning in warnings:
        print(warning)
    
    print()
    if passed:
        print("✅ ALL GATES PASSED - Release approved")
        return 0
    else:
        print("🚫 GATES FAILED - Release BLOCKED")
        print("\nFix quality issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
