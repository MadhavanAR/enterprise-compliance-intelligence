import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
from rag.config import OLLAMA_URL, OLLAMA_MODEL
from rag.logger import logger

SYSTEM_PROMPT = """You are a RAG assistant.
Answer ONLY from the given context.
If the answer is not in the context, say "I don't know".
Do not expand acronyms unless explicitly defined in the context.
"""

def generate_answer(question: str, context: list[str]) -> str:
    """Generate answer using Ollama with error handling."""
    logger.info(f"Generating answer for question: {question[:50]}...")
    logger.debug(f"Using {len(context)} context documents")
    prompt = f"""
{SYSTEM_PROMPT}

Context:
{chr(10).join(context)}

Question:
{question}

Answer:
"""

    try:
        logger.info(f"Calling Ollama API: {OLLAMA_URL} with model {OLLAMA_MODEL}")
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        answer = response.json()["response"]
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