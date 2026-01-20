"""
Confidence Scoring: Risk level estimation
- Based on documents used, claim coverage, metadata match
- Returns confidence score 0-1 with reasoning
"""
import json
import re
from typing import Dict, Any, Optional, TypedDict, cast
from pathlib import Path
import requests
from rag.config import (
    OLLAMA_URL, OLLAMA_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, LLM_TIMEOUT
)
from rag.logger import get_logger

# Load confidence estimator prompt
_PROMPT_PATH = Path(__file__).parent / "prompts" / "confidence_estimator_prompt.txt"
CONFIDENCE_ESTIMATOR_PROMPT = _PROMPT_PATH.read_text() if _PROMPT_PATH.exists() else """You are a confidence estimator for a RAG system.

Based on:
- number of documents used
- claim coverage
- metadata match strength

Return a confidence score between 0 and 1.

DO NOT rewrite the answer.
Return ONLY valid JSON.
"""

# Output schema
CONFIDENCE_SCHEMA = {
    "confidence": 0.0,
    "confidence_reason": "string"
}

class ConfidenceResult(TypedDict):
    confidence: float
    confidence_reason: str


def _fail_closed(reason: str) -> ConfidenceResult:
    # Enterprise-safe: if estimator fails, confidence must be 0.0.
    return {"confidence": 0.0, "confidence_reason": reason}


def _extract_json(raw_output: str) -> Optional[str]:
    m = re.search(r'```json\s*(\{.*?\})\s*```', raw_output, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'\{.*\}', raw_output, re.DOTALL)
    if m:
        return m.group(0)
    return None


def _validate_confidence(obj: Any) -> Optional[ConfidenceResult]:
    if not isinstance(obj, dict):
        return None
    raw_c = obj.get("confidence", 0.0)
    try:
        c = float(raw_c)
    except Exception:
        return None
    c = max(0.0, min(1.0, c))
    r = obj.get("confidence_reason", "")
    if not isinstance(r, str):
        r = "estimator_invalid_reason"
    return {"confidence": c, "confidence_reason": r}


def estimate_confidence(
    claims_count: int,
    sources_used: int,
    metadata_match: bool = True,
    rerank_score_avg: Optional[float] = None,
    trace_id: str = None
) -> Dict[str, Any]:
    """
    Estimate confidence score based on multiple factors.
    
    Args:
        claims_count: Number of claims in the answer
        sources_used: Number of source documents used
        metadata_match: Whether metadata filters matched
        rerank_score_avg: Average rerank score (optional)
        trace_id: Trace ID for logging
    
    Returns:
        {
            "confidence": float (0.0-1.0),
            "confidence_reason": str
        }
    """
    logger = get_logger(trace_id)
    logger.start_timer("confidence_estimation")
    logger.info("Estimating confidence",
                claims_count=claims_count,
                sources_used=sources_used,
                metadata_match=metadata_match,
                rerank_score_avg=rerank_score_avg)
    
    # Build input for confidence estimator
    input_data = {
        "claims_count": claims_count,
        "sources_used": sources_used,
        "metadata_match": metadata_match,
        "rerank_score_avg": rerank_score_avg
    }
    
    # Build prompt
    input_json = json.dumps(input_data, indent=2)
    prompt = f"""{CONFIDENCE_ESTIMATOR_PROMPT}

Input:
```json
{input_json}
```

Output Schema:
```json
{json.dumps(CONFIDENCE_SCHEMA, indent=2)}
```

Return ONLY valid JSON, no other text."""
    
    try:
        # Call Ollama for confidence estimation
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Deterministic confidence
                    "num_predict": 256,  # Short response (JSON only)
                }
            },
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        raw_output = result.get("response", "").strip()
        
        json_str = _extract_json(raw_output) or raw_output
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            logger.error("Confidence estimator JSON parse failed", raw_output=raw_output[:200])
            return _fail_closed("estimator_failed")

        validated = _validate_confidence(parsed)
        if not validated:
            logger.error("Confidence estimator returned invalid shape", raw_output=raw_output[:200])
            return _fail_closed("estimator_failed")
        
        result = validated
        
        logger.end_timer("confidence_estimation", confidence=result["confidence"])
        logger.info("Confidence estimation complete", confidence=result["confidence"])
        
        return result
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error("Failed to parse confidence JSON", error=str(e), raw_output=(raw_output or "")[:200])
        return _fail_closed("estimator_failed")
    except Exception as e:
        logger.error("Confidence estimation failed", error=str(e))
        return _fail_closed("estimator_failed")


def _rule_based_confidence(
    claims_count: int,
    sources_used: int,
    metadata_match: bool,
    rerank_score_avg: Optional[float]
) -> float:
    """
    Rule-based confidence fallback (deterministic).
    
    Factors:
    - More sources = higher confidence
    - More claims = higher confidence
    - Metadata match = bonus
    - Rerank score = quality signal
    """
    base_confidence = 0.5
    
    # Sources factor (0.0 - 0.3)
    sources_factor = min(0.3, sources_used * 0.1)
    
    # Claims factor (0.0 - 0.2)
    claims_factor = min(0.2, claims_count * 0.05)
    
    # Metadata match bonus (0.0 - 0.1)
    metadata_bonus = 0.1 if metadata_match else 0.0
    
    # Rerank score factor (0.0 - 0.2)
    rerank_factor = 0.0
    if rerank_score_avg is not None:
        rerank_factor = min(0.2, rerank_score_avg * 0.2)
    
    confidence = base_confidence + sources_factor + claims_factor + metadata_bonus + rerank_factor
    return max(0.0, min(1.0, confidence))
