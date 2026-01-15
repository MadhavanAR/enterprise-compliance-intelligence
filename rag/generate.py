import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"

SYSTEM_PROMPT = """You are a RAG assistant.
Answer ONLY from the given context.
If the answer is not in the context, say "I don't know".
Do not expand acronyms unless explicitly defined in the context.
"""

def generate_answer(question: str, context: list[str]) -> str:
    """Generate answer using Ollama with error handling."""
    prompt = f"""
{SYSTEM_PROMPT}

Context:
{chr(10).join(context)}

Question:
{question}

Answer:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()["response"]
    except ConnectionError:
        raise RuntimeError(
            f"Could not connect to Ollama at {OLLAMA_URL}. "
            "Please ensure Ollama is running: 'ollama serve'"
        )
    except Timeout:
        raise RuntimeError(
            "Ollama request timed out. The model may be taking too long to respond."
        )
    except RequestException as e:
        raise RuntimeError(f"Ollama API error: {str(e)}")
    except KeyError:
        raise RuntimeError(
            "Unexpected response format from Ollama. Please check the API response."
        )