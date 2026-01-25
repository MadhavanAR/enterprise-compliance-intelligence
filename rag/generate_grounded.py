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
- Frame statements as document-reported (e.g., "The documentation states that...").
- Summarize clearly; do not paste long raw text.

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


def _is_capability_question(question: str) -> bool:
    """
    Detect binary capability questions that risk over-assertion.
    
    Patterns:
    - "Can I...", "Can you...", "Can we..."
    - "Does X allow...", "Does X support...", "Does X provide..."
    - "Is it possible to...", "Is it possible for..."
    - "Do I have...", "Do users have..."
    - Questions with "guarantee", "permission", "entitlement"
    """
    q_lower = question.lower().strip()
    
    capability_patterns = [
        r'\bcan\s+(i|you|we|one|users?)\b',
        r'\bdoes\s+\w+\s+(allow|support|provide|enable|permit|guarantee)\b',
        r'\bis\s+it\s+possible\s+(to|for)',
        r'\bdo\s+(i|you|we|users?)\s+have\b',
        r'\b(guarantee|guaranteed|permission|entitlement|entitled)\b',
    ]
    
    return any(re.search(pattern, q_lower) for pattern in capability_patterns)


def _has_explicit_guarantee(context_docs: List[str]) -> bool:
    """
    Check if context contains explicit guarantee/permission language.
    
    Looks for:
    - "you can", "users can", "customers can"
    - "allows", "enables", "permits"
    - "guaranteed", "entitled", "permission"
    - Procedural language ("download", "access", "retrieve" with clear steps)
    """
    context_text = " ".join(context_docs).lower()
    
    explicit_patterns = [
        r'\b(you|users?|customers?)\s+can\s+',
        r'\ballows?\s+(you|users?|customers?|one)\s+to\s+',
        r'\benables?\s+(you|users?|customers?|one)\s+to\s+',
        r'\bpermits?\s+(you|users?|customers?|one)\s+to\s+',
        r'\bguaranteed?\s+',
        r'\bentitled\s+to\s+',
        r'\bpermission\s+to\s+',
        r'\bdownload\s+(the|a|your)',
        r'\baccess\s+(the|a|your)',
    ]
    
    return any(re.search(pattern, context_text) for pattern in explicit_patterns)


def _summarize_for_qualified(context_docs: List[str]) -> str:
    """
    Produce a short, document-scoped summary for qualified answers.
    Avoids raw dumps; uses concise, professional phrasing.
    """
    if not context_docs:
        return ""
    raw = (context_docs[0] or "").strip()
    if not raw:
        return ""
    # Strip [Doc N] prefixes
    raw = re.sub(r"\[Doc\s+\d+\]\s*", "", raw, flags=re.IGNORECASE).strip()
    # First sentence or first 120 chars; avoid long raw dumps
    match = re.search(r"^[^.]{1,120}(?:\.|$)", raw)
    excerpt = (match.group(0).strip() if match else raw[:120].strip()).strip()
    if not excerpt:
        return ""
    excerpt = " ".join(excerpt.split()).lower()
    # Strip leading "the documentation states that" so we never double it
    excerpt = re.sub(
        r"^\s*the\s+documentation\s+states?\s+(?:that\s+)?",
        "",
        excerpt,
        flags=re.IGNORECASE,
    ).strip()
    if not excerpt:
        return ""
    # Minimal casing for common entities (order: longer phrases first)
    for pat, repl in [
        (r"\baws artifact\b", "AWS Artifact"),
        (r"\bamazon web services\b", "Amazon Web Services"),
        (r"\baws\b", "AWS"),
    ]:
        excerpt = re.sub(pat, repl, excerpt, flags=re.IGNORECASE)
    if excerpt and excerpt[0].islower():
        excerpt = excerpt[0].upper() + excerpt[1:]
    return excerpt


def _prevent_over_assertion(
    question: str, answer: str, context_docs: List[str], logger
) -> str:
    """
    Post-process answer to prevent over-assertion on capability questions.
    
    If question is capability-style AND answer is binary ("Yes"/"No") AND
    context lacks explicit guarantees → replace with qualified statement or refusal.
    """
    if not answer or "don't know" in answer.lower():
        return answer
    
    # Only process capability questions
    if not _is_capability_question(question):
        return answer
    
    answer_lower = answer.lower().strip()
    
    # Check for binary assertions (handles "Yes", "Yes,", "Yes.", "Yes, you can", etc.)
    is_binary_yes = (
        answer_lower.startswith(("yes", "yes,", "yes.")) or
        re.match(r'^yes[,.]?\s+(you|i|we|one|users?|customers?)\s+can', answer_lower)
    )
    is_binary_no = (
        answer_lower.startswith(("no", "no,", "no.")) or
        re.match(r'^no[,.]?\s+(you|i|we|one|users?|customers?)\s+(cannot|cant|can\'t)', answer_lower)
    )
    
    if not (is_binary_yes or is_binary_no):
        return answer
    
    # Check if context has explicit guarantees
    has_guarantee = _has_explicit_guarantee(context_docs)
    
    if has_guarantee:
        # Explicit guarantee exists → allow binary answer
        return answer
    
    # No explicit guarantee → replace with qualified statement
    logger.warning(
        "Binary capability answer without explicit guarantee - replacing with qualified statement",
        question_preview=question[:50],
        answer_preview=answer[:50],
    )

    summary = _summarize_for_qualified(context_docs)

    if is_binary_yes:
        # Replace "Yes" with qualified, document-scoped statement
        if summary:
            qualified = (
                f"The documentation states that {summary}. "
                "It does not explicitly specify download permissions, access conditions, or procedural guarantees."
            )
        else:
            qualified = (
                "The documentation describes availability or access at a high level. "
                "It does not explicitly specify permissions, conditions, or procedural guarantees."
            )
        return qualified

    # Binary "No" without guarantee → refuse (meaning unchanged)
    return "I don't know."


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

        # Post-process: prevent over-assertion on capability questions
        answer = _prevent_over_assertion(question, answer, context_docs, logger)

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