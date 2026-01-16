"""
Query Router: Intent classification and routing decision
- Analyzes queries to determine: RAG vs Web vs Refuse
- Extracts metadata filters from queries
- Sets confidence requirements
"""
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
import requests
from rag.config import (
    OLLAMA_URL, OLLAMA_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, LLM_TIMEOUT
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
    
    try:
        # Call Ollama for routing decision
        response = requests.post(
            OLLAMA_URL,
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
        
        # Parse JSON
        routing_decision = json.loads(json_str)
        
        # Validate and set defaults
        routing_decision = {
            "intent": routing_decision.get("intent", "unknown"),
            "use_rag": routing_decision.get("use_rag", False),
            "use_web": routing_decision.get("use_web", False),
            "refuse": routing_decision.get("refuse", False),
            "metadata_filters": routing_decision.get("metadata_filters", {}),
            "confidence_requirement": routing_decision.get("confidence_requirement", "medium")
        }
        
        # Clean metadata filters (remove None values)
        metadata_filters = {}
        filters = routing_decision.get("metadata_filters", {})
        if filters.get("author"):
            metadata_filters["author"] = filters["author"]
        if filters.get("source"):
            metadata_filters["source"] = filters["source"]
        routing_decision["metadata_filters"] = metadata_filters if metadata_filters else None
        
        logger.end_timer("query_routing", 
                        intent=routing_decision["intent"],
                        use_rag=routing_decision["use_rag"],
                        use_web=routing_decision["use_web"],
                        refuse=routing_decision["refuse"])
        logger.info("Query routing complete", decision=routing_decision)
        
        return routing_decision
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse routing decision JSON", error=str(e), raw_output=raw_output[:200])
        # Fallback: safe defaults
        return {
            "intent": "unknown",
            "use_rag": True,  # Default to RAG
            "use_web": False,
            "refuse": False,
            "metadata_filters": None,
            "confidence_requirement": "medium"
        }
    except Exception as e:
        logger.error("Query routing failed", error=str(e))
        # Fallback: safe defaults
        return {
            "intent": "unknown",
            "use_rag": True,  # Default to RAG
            "use_web": False,
            "refuse": False,
            "metadata_filters": None,
            "confidence_requirement": "medium"
        }
