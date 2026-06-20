"""
Shared LLM provider for all Project DNA features.
Uses Groq API (llama-3.1-8b-instant) for fast, reliable inference.
"""
from groq import Groq
from django.conf import settings


def generate_ai_response(prompt, max_tokens=1000, retries=3, backoff_factor=2):
    """
    Generate AI response using Groq API.

    Args:
        prompt: The input prompt string
        max_tokens: Maximum tokens in response (default 1000)
        retries: Number of retries for transient failures (default 3)
        backoff_factor: Exponential backoff multiplier (default 2)

    Returns:
        Generated text response string

    Raises:
        RuntimeError: If API key not configured or all retries exhausted
    """
    if not settings.GROQ_API_KEY:
        return "ERROR: Groq API key not configured. Set GROQ_API_KEY in Backend/.env"

    client = Groq(api_key=settings.GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as exc:
        raise RuntimeError(f"AI service error: {exc}")
