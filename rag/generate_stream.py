"""
Streaming answer generation (FAANG-grade UX)
Yields tokens incrementally for ChatGPT-like experience
"""
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
2. Only say "I don't know" if context has NO relevant information.
3. Do NOT add commentary, notes, or explanations about what you don't know.
4. Do NOT use outside knowledge.
5. Cite each claim with [Doc 1] or [Doc 2] from available documents.
6. Answer directly and concisely. No meta-commentary.

Example:
Context: [Doc 1] BM25 is used in hybrid RAG systems for keyword search.
Question: What is BM25?
Answer: BM25 is used in hybrid RAG systems for keyword search [Doc 1].
"""

def generate_answer_stream(question: str, context: list[str], trace_id: str = None):
    """
    Generate answer with streaming (yields tokens incrementally).
    
    Yields:
        str: Incremental tokens as they're generated
    """
    logger = get_logger(trace_id)
    
    # Config-driven context limit
    context_docs = context[:CONTEXT_LIMIT]
    
    logger.start_timer("generation")
    logger.info("Starting streaming answer generation", 
                question_preview=question[:50],
                context_docs=len(context_docs))
    
    # Format context with document numbers for citations
    formatted_context = []
    for i, doc in enumerate(context_docs, 1):
        formatted_context.append(f"[Doc {i}] {doc}")
    
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
        logger.info("Calling Ollama API (streaming)",
                   url=OLLAMA_URL,
                   model=OLLAMA_MODEL,
                   temperature=LLM_TEMPERATURE)
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                }
            },
            timeout=LLM_TIMEOUT,
            stream=True  # Important for streaming
        )
        response.raise_for_status()
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = line.decode('utf-8')
                    # Ollama streams JSON lines
                    import json
                    data = json.loads(chunk)
                    
                    if "response" in data:
                        token = data["response"]
                        full_answer += token
                        yield token  # Yield token immediately
                    
                    if data.get("done", False):
                        # Final stats
                        prompt_tokens = data.get("prompt_eval_count", 0)
                        completion_tokens = data.get("eval_count", 0)
                        logger.log_token_usage(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=prompt_tokens + completion_tokens
                        )
                        logger.end_timer("generation", 
                                        answer_length=len(full_answer),
                                        prompt_tokens=prompt_tokens,
                                        completion_tokens=completion_tokens)
                        break
                except (json.JSONDecodeError, KeyError):
                    continue
        
        logger.info("Streaming answer generation complete")
        
    except ConnectionError as e:
        error_msg = (
            f"Could not connect to Ollama at {OLLAMA_URL}. "
            "Please ensure Ollama is running: 'ollama serve'. "
            f"Error: {str(e)}"
        )
        logger.error("Connection error", error=str(e))
        raise RuntimeError(error_msg)
    except Timeout:
        error_msg = "Ollama request timed out. The model may be taking too long to respond."
        logger.error("Timeout error")
        raise RuntimeError(error_msg)
    except RequestException as e:
        error_msg = f"Ollama API error: {str(e)}"
        logger.error("Request error", error=str(e))
        raise RuntimeError(error_msg)
