import os
from openai import OpenAI
from openai import RateLimitError, APIError

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a RAG assistant.
Answer ONLY from the given context.
If the answer is not in the context, say "I don't know".
"""

def generate_answer(question: str, context: list[str]) -> str:
    """Generate answer using OpenAI API with error handling."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    joined_context = "\n\n".join(context)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Context:\n{joined_context}\n\nQuestion:\n{question}"
                }
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content
    except RateLimitError as e:
        error_msg = "OpenAI API quota exceeded. Please check your billing details."
        raise RuntimeError(error_msg) from e
    except APIError as e:
        error_msg = f"OpenAI API error: {str(e)}"
        raise RuntimeError(error_msg) from e