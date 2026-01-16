import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
from rag.config import (
    OLLAMA_URL, OLLAMA_MODEL, LLM_TEMPERATURE, 
    LLM_MAX_TOKENS, LLM_TIMEOUT, CONTEXT_LIMIT
)
from rag.logger import get_logger

SYSTEM_PROMPT = """Answer the question using ONLY information from the provided context.

RULES:
1. Use information from the context to answer. If context mentions the topic, use it.
2. If context is empty or has NO relevant information, you MUST respond with exactly: "I don't know."
3. Do NOT add commentary, notes, or explanations about what you don't know.
4. Do NOT use outside knowledge.
5. Cite each claim with [Doc 1] or [Doc 2] from available documents.
6. Answer directly and concisely. No meta-commentary.

Example:
Context: [Doc 1] BM25 is used in hybrid RAG systems for keyword search.
Question: What is BM25?
Answer: BM25 is used in hybrid RAG systems for keyword search [Doc 1].

Example (empty context):
Context: (empty)
Question: What is BM25?
Answer: I don't know.
"""

def generate_answer(question: str, context: list[str], trace_id: str = None) -> str:
    """
    Generate answer using Ollama with error handling and observability.
    
    HARD REFUSAL GUARANTEE: Returns "I don't know" if context is empty.
    """
    logger = get_logger(trace_id)
    
    # HARD REFUSAL GUARANTEE: Guard logic (not just prompt)
    if not context or all(not doc.strip() for doc in context):
        logger.warning("Empty context detected - enforcing hard refusal")
        return "I don't know."
    
    # Config-driven context limit (FAANG-grade: deterministic)
    context_docs = context[:CONTEXT_LIMIT]
    
    # Filter out empty docs
    context_docs = [doc for doc in context_docs if doc.strip()]
    
    # HARD REFUSAL GUARANTEE: Double-check after filtering
    if not context_docs:
        logger.warning("All context docs are empty - enforcing hard refusal")
        return "I don't know."
    
    logger.start_timer("generation")
    logger.info("Starting answer generation", 
                question_preview=question[:50],
                context_docs=len(context_docs),
                context_limit=CONTEXT_LIMIT)
    
    # Format context with document numbers for citations
    formatted_context = []
    for i, doc in enumerate(context_docs, 1):
        formatted_context.append(f"[Doc {i}] {doc}")
    
    # Add explicit instruction about available documents
    doc_list = ", ".join([f"[Doc {i}]" for i in range(1, len(context_docs) + 1)])
    
    prompt = f"""
{SYSTEM_PROMPT}

Available documents: {doc_list}
You can ONLY cite these documents. Do NOT cite documents that do not exist.

Context:
{chr(10).join(formatted_context)}

Question:
{question}

Answer (cite only from available documents above):
"""

    try:
        logger.info("Calling Ollama API",
                   url=OLLAMA_URL,
                   model=OLLAMA_MODEL,
                   temperature=LLM_TEMPERATURE,
                   max_tokens=LLM_MAX_TOKENS)
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,  # Deterministic (FAANG-grade)
                    "num_predict": LLM_MAX_TOKENS,   # Cap output length
                }
            },
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        answer = result["response"]
        
        # Log token usage if available
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens
        logger.log_token_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        
        logger.end_timer("generation", 
                        answer_length=len(answer),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens)
        logger.info("Answer generated successfully")
        return answer
    except ConnectionError as e:
        raise RuntimeError(
            f"Could not connect to Ollama at {OLLAMA_URL}. "
            "Please ensure Ollama is running: 'ollama serve'. "
            f"Error: {str(e)}"
        )
    except Timeout:
        raise RuntimeError(
            "Ollama request timed out. The model may be taking too long to respond."
        )
    except requests.exceptions.HTTPError as e:
        error_msg = f"Ollama API HTTP error: {str(e)}"
        if hasattr(e.response, 'url'):
            error_msg += f" (URL: {e.response.url})"
        if e.response.status_code == 405:
            error_msg += (
                f"\nMethod not allowed. Check that OLLAMA_URL is correct: {OLLAMA_URL}. "
                "Expected format: http://localhost:11434/api/generate"
            )
        raise RuntimeError(error_msg)
    except RequestException as e:
        raise RuntimeError(f"Ollama API error: {str(e)}")
    except KeyError:
        raise RuntimeError(
            "Unexpected response format from Ollama. Please check the API response."
        )