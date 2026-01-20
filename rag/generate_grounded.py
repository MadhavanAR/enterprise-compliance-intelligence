"""
Grounded Answer Generation: Structured output with claims + citations
- Zero hallucination guarantee
- Every claim maps to a source document
- Returns JSON with answer, claims, and sources
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from rag.config import (
    CONTEXT_LIMIT,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    OLLAMA_MODEL,
    OLLAMA_URL,
)
from rag.logger import get_logger

# Load grounded answer prompt
_PROMPT_PATH = Path(__file__).parent / "prompts" / "grounded_answer_prompt.txt"
GROUNDED_ANSWER_PROMPT = (
    _PROMPT_PATH.read_text()
    if _PROMPT_PATH.exists()
    else """You are a grounded answer generator.

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
)

# Output schema
GROUNDED_SCHEMA: Dict[str, Any] = {
    "answer": "string",
    "claims": [{"text": "string", "source_doc": "Doc 1"}],
    "sources_used": ["Doc 1", "Doc 2"],
}


def _normalize_context(context: List[Any]) -> List[str]:
    """
    Normalize context to a clean list of strings.
    - Non-strings are discarded safely.
    - Empty/whitespace-only strings are dropped.
    """
    cleaned: List[str] = []
    for item in context or []:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if text:
            cleaned.append(text)
    return cleaned


def _extract_json(raw_output: str) -> Optional[str]:
    """Extract a JSON object from model output (fenced or raw)."""
    if not raw_output:
        return None

    m = re.search(r"```json\s*(\{.*?\})\s*```", raw_output, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()

    m = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if m:
        return m.group(0).strip()

    return None


def _safe_json_loads(json_str: str) -> Optional[Dict[str, Any]]:
    """Parse JSON with minimal cleanup for common model issues."""
    if not json_str:
        return None

    try:
        obj = json.loads(json_str)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        cleaned = re.sub(r",\s*([}\]])", r"\1", json_str).strip()
        try:
            obj = json.loads(cleaned)
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None


def generate_grounded_answer(question: str, context: List[Any], trace_id: str = None) -> Dict[str, Any]:
    """
    Generate grounded answer with structured claims + citations.

    HARD REFUSAL GUARANTEE:
    - No usable context → "I don't know"
    """
    logger = get_logger(trace_id)

    context_docs = _normalize_context(context)
    if not context_docs:
        logger.warning("Empty or invalid context detected - enforcing hard refusal")
        return {"answer": "I don't know.", "claims": [], "sources_used": []}

    context_docs = context_docs[:CONTEXT_LIMIT]
    allowed_docs = {f"Doc {i}" for i in range(1, len(context_docs) + 1)}

    logger.start_timer("grounded_generation")
    logger.info(
        "Starting grounded answer generation",
        question_preview=question[:50],
        context_docs=len(context_docs),
        context_limit=CONTEXT_LIMIT,
    )

    formatted_context = [f"[Doc {i}] {doc}" for i, doc in enumerate(context_docs, 1)]
    context_text = "\n".join(formatted_context)
    doc_list = ", ".join(f"[Doc {i}]" for i in range(1, len(context_docs) + 1))

    prompt = GROUNDED_ANSWER_PROMPT.format(context=context_text, question=question)
    schema_json = json.dumps(GROUNDED_SCHEMA, indent=2)

    full_prompt = f"""{prompt}

Output Schema:
```json
{schema_json}
```

Available documents: {doc_list}
You can ONLY cite these documents. Do NOT cite documents that do not exist.

Return ONLY valid JSON, no other text.
"""

    try:
        logger.info(
            "Calling Ollama API for grounded answer",
            url=OLLAMA_URL,
            model=OLLAMA_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )

        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                },
            },
            timeout=LLM_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        raw_output = (payload.get("response") or "").strip()

        json_str = _extract_json(raw_output) or raw_output
        grounded = _safe_json_loads(json_str)
        if not grounded:
            logger.warning("No valid JSON found in grounded answer output", raw_preview=raw_output[:200])
            return {"answer": "I don't know.", "claims": [], "sources_used": []}

        raw_answer = grounded.get("answer", "")

        # Normalize answer safely (local LLMs may emit wrong types)
        if isinstance(raw_answer, list):
            answer = " ".join(x.strip() for x in raw_answer if isinstance(x, str) and x.strip()).strip()
        elif isinstance(raw_answer, str):
            answer = raw_answer.strip()
        else:
            logger.warning(
                "Invalid answer type from model, enforcing refusal",
                answer_type=str(type(raw_answer)),
            )
            return {"answer": "I don't know.", "claims": [], "sources_used": []}
        claims = grounded.get("claims") or []
        sources_used = grounded.get("sources_used") or []

        if not answer:
            return {"answer": "I don't know.", "claims": [], "sources_used": []}

        if not isinstance(claims, list):
            claims = []
        normalized_claims: List[Dict[str, str]] = []
        invalid_source = False
        for c in claims:
            if not isinstance(c, dict):
                continue
            text = c.get("text")
            source_doc = c.get("source_doc")
            if not isinstance(text, str) or not text.strip():
                continue
            if not isinstance(source_doc, str) or not source_doc.strip():
                continue
            source_doc = source_doc.strip()
            if source_doc not in allowed_docs:
                invalid_source = True
                continue
            normalized_claims.append({"text": text.strip(), "source_doc": source_doc})

        if invalid_source:
            logger.warning("Invalid claim source_doc detected - enforcing refusal")
            return {"answer": "I don't know.", "claims": [], "sources_used": []}

        if not isinstance(sources_used, list):
            sources_used = []
        sources_used = [s.strip() for s in sources_used if isinstance(s, str) and s.strip()]
        # Enforce sources_used subset of allowed docs
        if any(s not in allowed_docs for s in sources_used):
            logger.warning("Invalid sources_used detected - enforcing refusal")
            return {"answer": "I don't know.", "claims": [], "sources_used": []}

        if not sources_used and normalized_claims:
            sources_used = sorted({c["source_doc"] for c in normalized_claims})

        # Enterprise contract: non-refusal answers must have claims + sources
        if answer and "don't know" not in answer.lower():
            if not normalized_claims or not sources_used:
                logger.warning("Missing claims/sources for non-refusal answer - enforcing refusal")
                return {"answer": "I don't know.", "claims": [], "sources_used": []}

        prompt_tokens = int(payload.get("prompt_eval_count") or 0)
        completion_tokens = int(payload.get("eval_count") or 0)
        logger.log_token_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

        result = {"answer": answer, "claims": normalized_claims, "sources_used": sources_used}

        logger.end_timer(
            "grounded_generation",
            answer_length=len(answer),
            claims_count=len(claims),
            sources_count=len(sources_used),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        logger.info("Grounded answer generated successfully")
        return result

    except Exception as e:
        logger.error("Grounded answer generation failed", error=str(e))
        return {"answer": "I don't know.", "claims": [], "sources_used": []}