"""
Enterprise Compliance Engine: Single canonical entry point.

FAANG-grade invariant:
- One entry point used by CLI, UI, demos, and future APIs.
- Fail-closed: on any error, return an explicit refusal payload.
- Never bypass guardrails (router, policy engine, retrieval, grounded generation, confidence).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import uuid

from rag.logger import get_logger
from rag.supervisor import build_supervisor
from rag.feature_flags import FeatureFlags


def _refusal_payload(question: str, trace_id: str, reason: str) -> Dict[str, Any]:
    # Keep shape stable for callers.
    return {
        "answer": "I don't know.",
        "claims": [],
        "sources_used": [],
        "confidence": 0.0,
        "confidence_reason": reason,
        "decision_path": "engine -> refuse",
        "intent": "unknown",
        "documents": [],
        "trace_id": trace_id,
        "refusal_reason": reason,
        "question": question,
    }


def run_enterprise_query(
    question: str,
    *,
    metadata_filters: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    feature_flags: Optional[FeatureFlags] = None,
) -> Dict[str, Any]:
    """
    Canonical query entry point.

    Always returns a stable, enterprise-auditable payload:
    {
      "answer": str,
      "claims": list,
      "sources_used": list,
      "confidence": float,
      "confidence_reason": str,
      "decision_path": str,
      "intent": str,
      "documents": list,
      "trace_id": str,
      "refusal_reason": optional str,
      "question": original question
    }
    """
    trace_id_value = trace_id or str(uuid.uuid4())
    logger = get_logger(trace_id_value)
    ff = feature_flags if feature_flags is not None else FeatureFlags()

    try:
        app = build_supervisor()
        payload: Dict[str, Any] = {
            "question": question,
            "trace_id": trace_id_value,
            "feature_flags": ff,
        }
        if metadata_filters:
            payload["metadata_filters"] = metadata_filters
        result = app.invoke(payload)

        # DEMO: minimal response when audit trail disabled
        if not ff.enable_audit_trail:
            return {
                "answer": result.get("answer", "") or "",
                "trace_id": result.get("trace_id") or trace_id_value,
                "question": question,
            }

        # Defensive extraction (fail-closed if missing critical fields)
        answer = result.get("answer", "")
        claims = result.get("claims", []) or []
        sources_used = result.get("sources_used", []) or []
        raw_confidence = result.get("confidence")
        confidence = None if raw_confidence is None else float(raw_confidence or 0.0)
        confidence_reason = result.get("confidence_reason", "") or ""
        intent = result.get("intent", "unknown") or "unknown"

        decision_path_raw = result.get("decision_path", [])
        if isinstance(decision_path_raw, list):
            decision_path = " -> ".join(str(x) for x in decision_path_raw if x)
        elif isinstance(decision_path_raw, str):
            decision_path = decision_path_raw
        else:
            decision_path = "unknown"

        documents = result.get("documents", []) or []

        refusal_reason = result.get("refusal_reason")
        if not refusal_reason and isinstance(answer, str) and "don't know" in answer.lower():
            refusal_reason = confidence_reason or "refused"

        # Minimal contract enforcement: never return partial ambiguous outputs
        if not isinstance(answer, str):
            return _refusal_payload(question, trace_id_value, "engine_invalid_answer_type")

        payload: Dict[str, Any] = {
            "answer": answer,
            "claims": claims if isinstance(claims, list) else [],
            "sources_used": sources_used if isinstance(sources_used, list) else [],
            "confidence": confidence,
            "confidence_reason": confidence_reason if isinstance(confidence_reason, str) else "engine_invalid_confidence_reason",
            "decision_path": decision_path,
            "intent": intent if isinstance(intent, str) else "unknown",
            "documents": documents if isinstance(documents, list) else [],
            "trace_id": result.get("trace_id") or trace_id_value,
            "question": question,
        }
        if refusal_reason:
            payload["refusal_reason"] = refusal_reason
        if result.get("unverified"):
            payload["unverified"] = True
        if result.get("generation_error"):
            payload["generation_error"] = str(result["generation_error"])

        return payload

    except Exception as e:
        logger.error("Engine execution failed", error=str(e))
        return _refusal_payload(question, trace_id_value, "engine_error")

