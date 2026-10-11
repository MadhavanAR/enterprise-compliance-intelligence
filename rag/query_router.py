"""
Query Router: Intent classification and routing decision
- Analyzes queries to determine: RAG vs Web vs Refuse
- Extracts metadata filters from queries
- Sets confidence requirements
"""
import json
import re
from typing import Dict, Any, Optional, TypedDict, Literal, cast
from pathlib import Path
import requests
from rag.config import (
    OLLAMA_URL, OLLAMA_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, LLM_TIMEOUT, OLLAMA_HEADERS
)
from rag.logger import get_logger

# Load query router prompt
_PROMPT_PATH = Path(__file__).parent / "prompts" / "query_router_prompt.txt"
QUERY_ROUTER_PROMPT = _PROMPT_PATH.read_text() if _PROMPT_PATH.exists() else """You are a Query Router for a production RAG system.

Your job is to analyze the user query and output a JSON decision.
You DO NOT answer the question.

Rules:
- If the question requires internal documents → use_rag = true
- If the question requires live facts → use_web = true
- If the question is opinion/speculation → refuse = true
- If author/source is mentioned → extract metadata filters
- Prefer refusal over hallucination

Return ONLY valid JSON matching the schema.

User query:
"{query}"
"""

# Output schema
ROUTER_SCHEMA = {
    "intent": "factual | analytical | opinion | unknown",
    "use_rag": True,
    "use_web": False,
    "refuse": False,
    "metadata_filters": {
        "author": None,
        "source": None
    },
    "confidence_requirement": "high | medium | low"
}

RouterAction = Literal["ALLOW_RAG", "ALLOW_WEB", "REFUSE"]
RouterIntent = Literal["factual", "analytical", "opinion", "unknown"]
ConfidenceRequirement = Literal["high", "medium", "low"]


class RouterDecision(TypedDict, total=False):
    intent: RouterIntent
    use_rag: bool
    use_web: bool
    refuse: bool
    metadata_filters: Optional[Dict[str, Any]]
    confidence_requirement: ConfidenceRequirement
    router_action: RouterAction


def _refuse_decision(reason: str = "router_failed") -> RouterDecision:
    # Fail-closed: explicit refusal is safer than ambiguous routing.
    return {
        "intent": "unknown",
        "use_rag": False,
        "use_web": False,
        "refuse": True,
        "metadata_filters": None,
        "confidence_requirement": "high",
        "router_action": "REFUSE",
        "refusal_reason": reason,  # extra field for logging/debug (ignored by schema consumers)
    }  # type: ignore[typeddict-item]


def _coerce_router_decision(raw: Any) -> RouterDecision:
    """
    Coerce and validate router output into a safe, deterministic shape.
    If anything is invalid/ambiguous -> REFUSE.
    """
    if not isinstance(raw, dict):
        return _refuse_decision("router_invalid_type")

    intent_raw = raw.get("intent", "unknown")
    intent: RouterIntent = intent_raw if intent_raw in ("factual", "analytical", "opinion", "unknown") else "unknown"

    use_rag = bool(raw.get("use_rag", True))
    use_web = bool(raw.get("use_web", False))
    refuse = bool(raw.get("refuse", False))

    # Normalize confidence requirement
    cr_raw = raw.get("confidence_requirement", "medium")
    confidence_requirement: ConfidenceRequirement = cr_raw if cr_raw in ("high", "medium", "low") else "medium"

    # Normalize metadata filters: accept dict or None, drop empties
    mf_raw = raw.get("metadata_filters")
    metadata_filters: Optional[Dict[str, Any]] = None
    if isinstance(mf_raw, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in mf_raw.items():
            if v is None:
                continue
            if isinstance(v, str) and not v.strip():
                continue
            cleaned[str(k)] = v
        metadata_filters = cleaned if cleaned else None

    # Determine canonical router action (MUST be exactly one)
    if refuse:
        router_action: RouterAction = "REFUSE"
        use_rag = False
        use_web = False
    elif use_web and not use_rag:
        router_action = "ALLOW_WEB"
    else:
        # Default to RAG when not refusing (enterprise-safe, internal KB first)
        router_action = "ALLOW_RAG"
        use_rag = True
        use_web = False

    return {
        "intent": intent,
        "use_rag": use_rag,
        "use_web": use_web,
        "refuse": router_action == "REFUSE",
        "metadata_filters": metadata_filters,
        "confidence_requirement": confidence_requirement,
        "router_action": router_action,
    }


def route_query(query: str, trace_id: str = None) -> Dict[str, Any]:
    """
    Route query: determine intent, routing decision, and metadata filters.
    
    Returns:
        {
            "intent": "factual | analytical | opinion | unknown",
            "use_rag": bool,
            "use_web": bool,
            "refuse": bool,
            "metadata_filters": {"author": str | None, "source": str | None},
            "confidence_requirement": "high | medium | low"
        }
    """
    logger = get_logger(trace_id)
    logger.start_timer("query_routing")
    logger.info("Starting query routing", query_preview=query[:50])

    # Fail-closed guardrail: empty or whitespace queries must be refused
    if not query or not query.strip():
        logger.info("Query Router: Empty or whitespace query detected - refusing")
        logger.end_timer("query_routing")
        return {
            "intent": "unknown",
            "use_rag": False,
            "use_web": False,
            "refuse": True,
            "metadata_filters": None,
            "confidence_requirement": "high",
            "router_action": "REFUSE",
            "refusal_reason": "Empty or whitespace-only query refused",
        }

    # Build prompt
    prompt = QUERY_ROUTER_PROMPT.format(query=query)
    
    # Add schema instruction
    schema_json = json.dumps(ROUTER_SCHEMA, indent=2)
    full_prompt = f"""{prompt}

Output Schema:
```json
{schema_json}
```

Return ONLY valid JSON, no other text."""
    
    raw_output = ""
    try:
        # Call Ollama for routing decision
        response = requests.post(
            OLLAMA_URL,
            headers=OLLAMA_HEADERS,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Deterministic routing
                    "num_predict": 512,  # Short response (JSON only)
                }
            },
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        raw_output = result.get("response", "").strip()
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            json_str = json_match.group(0) if json_match else raw_output
        
        parsed = json.loads(json_str)
        routing_decision = _coerce_router_decision(parsed)
        
        logger.end_timer(
            "query_routing",
            intent=routing_decision.get("intent"),
            use_rag=routing_decision.get("use_rag"),
            use_web=routing_decision.get("use_web"),
            refuse=routing_decision.get("refuse"),
            router_action=routing_decision.get("router_action"),
        )
        logger.info("Query routing complete", decision=routing_decision)
        
        return routing_decision
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse routing decision JSON", error=str(e), raw_output=(raw_output or "")[:200])
        return cast(Dict[str, Any], _refuse_decision("router_json_parse_failed"))
    except Exception as e:
        logger.error("Query routing failed", error=str(e))
        return cast(Dict[str, Any], _refuse_decision("router_request_failed"))
