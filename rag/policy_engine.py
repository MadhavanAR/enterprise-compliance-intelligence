"""
Policy Engine: Config-driven, deterministic policy evaluation
- Evaluates policies BEFORE retrieval (no LLM calls)
- Policies are deterministic and fast
- Logged in decision_path for auditability
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from rag.logger import get_logger

# Load policies from config
_POLICY_PATH = Path(__file__).parent.parent / "policies.yaml"
_policies = {}

if _POLICY_PATH.exists():
    with open(_POLICY_PATH, "r") as f:
        _policies = yaml.safe_load(f) or {}
else:
    # Default policies if file doesn't exist
    _policies = {
        "policies": {
            "blocked_intents": [],
            "confidence_thresholds": {
                "default": 0.5
            },
            "strict_metadata_match": True,
            "refuse_on_zero_docs": True,
            "refuse_on_low_confidence": False
        }
    }


def evaluate_policies(
    intent: str,
    confidence_requirement: str = "medium",
    metadata_filters: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate policies BEFORE retrieval.
    
    Policies are deterministic, fast, and require no LLM calls.
    
    Args:
        intent: Query intent ("factual" | "analytical" | "opinion" | "medical_advice", etc.)
        confidence_requirement: Confidence requirement level ("high" | "medium" | "low")
        metadata_filters: Metadata filters to apply
        trace_id: Trace ID for logging
    
    Returns:
        {
            "allowed": bool,
            "refuse": bool,
            "reason": str,
            "confidence_threshold": float,
            "policy_violations": List[str]
        }
    """
    logger = get_logger(trace_id)
    logger.info("Evaluating policies", intent=intent, confidence_requirement=confidence_requirement)
    
    policy_config = _policies.get("policies", {})
    policy_violations = []
    
    # Policy 1: Block specific intents
    blocked_intents = policy_config.get("blocked_intents", [])
    if intent in blocked_intents:
        policy_violations.append(f"Intent '{intent}' is blocked by policy")
        logger.warning("Policy violation: Blocked intent", intent=intent)
        return {
            "allowed": False,
            "refuse": True,
            "reason": f"Intent '{intent}' is blocked by enterprise policy",
            "confidence_threshold": 1.0,  # Require maximum confidence (effectively block)
            "policy_violations": policy_violations
        }
    
    # Policy 2: Confidence thresholds
    confidence_thresholds = policy_config.get("confidence_thresholds", {})
    
    # Map intent to risk level for threshold lookup
    high_risk_intents = ["medical_advice", "financial_advice", "legal_advice"]
    if intent in high_risk_intents:
        risk_level = "high_risk_intents"
    elif intent in ["opinion", "speculation"]:
        risk_level = "medium_risk_intents"
    else:
        risk_level = "default"
    
    # Get confidence threshold
    confidence_threshold = confidence_thresholds.get(risk_level) or confidence_thresholds.get("default", 0.5)
    
    # Policy 3: Strict metadata match (if enabled)
    strict_metadata_match = policy_config.get("strict_metadata_match", True)
    if strict_metadata_match and metadata_filters:
        # Metadata filters are enforced at retrieval level, but we log policy here
        logger.info("Policy: Strict metadata match enforced", filters=metadata_filters)
    
    # Policy 4: Refuse on zero docs (enforced at retrieval level, logged here)
    refuse_on_zero_docs = policy_config.get("refuse_on_zero_docs", True)
    if refuse_on_zero_docs:
        logger.debug("Policy: Refuse on zero documents enabled")
    
    # Policy 5: Refuse on low confidence (evaluated after answer generation)
    refuse_on_low_confidence = policy_config.get("refuse_on_low_confidence", False)
    
    # No violations - allow processing
    logger.info("Policies evaluated", 
                allowed=True,
                confidence_threshold=confidence_threshold,
                violations_count=len(policy_violations))
    
    return {
        "allowed": True,
        "refuse": False,
        "reason": None,
        "confidence_threshold": confidence_threshold,
        "refuse_on_low_confidence": refuse_on_low_confidence,
        "policy_violations": policy_violations
    }


def check_post_generation_policy(
    confidence: float,
    confidence_threshold: float,
    refuse_on_low_confidence: bool,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check policies AFTER answer generation (confidence-based refusal).
    
    This is called after answer generation to enforce confidence thresholds.
    
    Args:
        confidence: Actual confidence score
        confidence_threshold: Required threshold from policy
        refuse_on_low_confidence: Whether to refuse on low confidence
        trace_id: Trace ID for logging
    
    Returns:
        {
            "allowed": bool,
            "refuse": bool,
            "reason": str
        }
    """
    logger = get_logger(trace_id)
    
    if not refuse_on_low_confidence:
        # Policy not enabled - allow regardless of confidence
        return {
            "allowed": True,
            "refuse": False,
            "reason": None
        }
    
    if confidence < confidence_threshold:
        logger.warning("Policy violation: Low confidence", 
                      confidence=confidence,
                      threshold=confidence_threshold)
        return {
            "allowed": False,
            "refuse": True,
            "reason": f"Confidence {confidence:.2f} below threshold {confidence_threshold:.2f}"
        }
    
    return {
        "allowed": True,
        "refuse": False,
        "reason": None
    }
