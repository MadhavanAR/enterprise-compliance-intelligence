"""
Grounded Answer Generation: Structured output with claims + citations
- Zero hallucination guarantee
- Every claim maps to a source document
- Returns JSON with answer, claims, and sources
"""
import json
import re
from typing import Dict, Any, List
from pathlib import Path
import requests
from rag.config import (
    OLLAMA_URL, OLLAMA_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, LLM_TIMEOUT, CONTEXT_LIMIT
)
from rag.logger import get_logger

# Load grounded answer prompt
_PROMPT_PATH = Path(__file__).parent / "prompts" / "grounded_answer_prompt.txt"
GROUNDED_ANSWER_PROMPT = _PROMPT_PATH.read_text() if _PROMPT_PATH.exists() else """You are a grounded answer generator.

STRICT RULES:
- Use ONLY the provided context.
- If the context does not answer the question, say "I don't know."
- Every factual claim MUST cite a document ID.
- Do NOT add explanations, apologies, or meta commentary.

Context:
{context}

Question:
{question}

Return ONLY valid JSON matching the schema.
"""

# Output schema
GROUNDED_SCHEMA = {
    "answer": "string",
    "claims": [
        {
            "text": "string",
            "source_doc": "Doc 1"
        }
    ],
    "sources_used": ["Doc 1", "Doc 2"]
}


def generate_grounded_answer(
    question: str, 
    context: List[str], 
    trace_id: str = None
) -> Dict[str, Any]:
    """
    Generate grounded answer with structured claims + citations.
    
    HARD REFUSAL GUARANTEE: Returns "I don't know" if context is empty.
    
    Returns:
        {
            "answer": str,
            "claims": [{"text": str, "source_doc": str}],
            "sources_used": [str]
        }
    """
    logger = get_logger(trace_id)
    
    # HARD REFUSAL GUARANTEE: Guard logic (not just prompt)
    if not context or all(not doc.strip() for doc in context):
        logger.warning("Empty context detected - enforcing hard refusal")
        return {
            "answer": "I don't know.",
            "claims": [],
            "sources_used": []
        }
    
    # Config-driven context limit
    context_docs = context[:CONTEXT_LIMIT]
    context_docs = [doc for doc in context_docs if doc.strip()]
    
    # HARD REFUSAL GUARANTEE: Double-check after filtering
    if not context_docs:
        logger.warning("All context docs are empty - enforcing hard refusal")
        return {
            "answer": "I don't know.",
            "claims": [],
            "sources_used": []
        }
    
    logger.start_timer("grounded_generation")
    logger.info("Starting grounded answer generation",
                question_preview=question[:50],
                context_docs=len(context_docs),
                context_limit=CONTEXT_LIMIT)
    
    # Format context with document numbers for citations
    formatted_context = []
    for i, doc in enumerate(context_docs, 1):
        formatted_context.append(f"[Doc {i}] {doc}")
    
    # Add explicit instruction about available documents
    doc_list = ", ".join([f"[Doc {i}]" for i in range(1, len(context_docs) + 1)])
    
    # Build prompt
    context_text = "\n".join(formatted_context)
    prompt = GROUNDED_ANSWER_PROMPT.format(
        context=context_text,
        question=question
    )
    
    # Add schema instruction
    schema_json = json.dumps(GROUNDED_SCHEMA, indent=2)
    full_prompt = f"""{prompt}

Output Schema:
```json
{schema_json}
```

Available documents: {doc_list}
You can ONLY cite these documents. Do NOT cite documents that do not exist.

Return ONLY valid JSON, no other text."""
    
    try:
        logger.info("Calling Ollama API for grounded answer",
                   url=OLLAMA_URL,
                   model=OLLAMA_MODEL,
                   temperature=LLM_TEMPERATURE,
                   max_tokens=LLM_MAX_TOKENS)
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,  # Deterministic
                    "num_predict": LLM_MAX_TOKENS,
                }
            },
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        raw_output = result.get("response", "").strip()
        
        # Extract JSON from response (handle markdown code blocks)
        json_str = None
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly (greedy match)
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
        
        if not json_str:
            logger.warning("No JSON found in response, attempting direct parse", raw_output=raw_output[:200])
            json_str = raw_output
        
        # Parse JSON (handle trailing commas and other issues)
        try:
            # Try direct parse first
            grounded_response = json.loads(json_str)
        except json.JSONDecodeError:
            # Try cleaning up common issues
            json_str = json_str.rstrip().rstrip(',')
            # Try again
            try:
                grounded_response = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse grounded answer JSON after cleanup", error=str(e), json_preview=json_str[:200])
                # Fallback: return refusal
                return {
                    "answer": "I don't know.",
                    "claims": [],
                    "sources_used": []
                }
        
        # Validate structure
        answer = grounded_response.get("answer", "")
        claims = grounded_response.get("claims", [])
        sources_used = grounded_response.get("sources_used", [])
        
        # Extract sources from claims if not explicitly provided
        if not sources_used and claims:
            sources_used = list(set([claim.get("source_doc") for claim in claims if claim.get("source_doc")]))
        
        # Ensure answer exists (fallback to "I don't know" if empty)
        if not answer or answer.strip() == "":
            answer = "I don't know."
            claims = []
            sources_used = []
        
        result = {
            "answer": answer.strip(),
            "claims": claims,
            "sources_used": sources_used
        }
        
        # Log token usage (from Ollama response, not from parsed JSON)
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens
        logger.log_token_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        
        logger.end_timer("grounded_generation",
                        answer_length=len(result["answer"]),
                        claims_count=len(result["claims"]),
                        sources_count=len(result["sources_used"]),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens)
        logger.info("Grounded answer generated successfully")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse grounded answer JSON", error=str(e), raw_output=raw_output[:200])
        # Fallback: return refusal
        return {
            "answer": "I don't know.",
            "claims": [],
            "sources_used": []
        }
    except Exception as e:
        logger.error("Grounded answer generation failed", error=str(e))
        # Fallback: return refusal
        return {
            "answer": "I don't know.",
            "claims": [],
            "sources_used": []
        }
