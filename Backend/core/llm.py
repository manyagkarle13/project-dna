"""
Shared LLM provider for all Project DNA features.
Uses Hugging Face Inference API (FREE) with retry handling for cold-start errors.
"""
import os
import time
import requests
from django.conf import settings


def generate_ai_response(prompt, max_tokens=1000, retries=3, backoff_factor=2):
    """
    Generate AI response using Hugging Face Inference API (mistralai/Mistral-7B-Instruct-v0.3).

    Args:
        prompt: The input prompt string
        max_tokens: Maximum tokens in response (default 1000)
        retries: Number of retries for transient failures (default 3)
        backoff_factor: Exponential backoff multiplier (default 2)

    Returns:
        Generated text response string

    Raises:
        ValueError: If token not configured or all retries exhausted
    """
    hf_token = os.environ.get('HUGGINGFACE_API_TOKEN') or os.environ.get('HUGGINGFACE_API_KEY')

    if not hf_token:
        # Also try from Django settings
        try:
            from django.conf import settings
            hf_token = getattr(settings, 'HUGGINGFACE_API_KEY', None) or getattr(settings, 'HUGGINGFACE_API_TOKEN', None)
        except:
            pass
    if not hf_token:
        return (
            "ERROR: Hugging Face API token not configured.\n"
            "Set HUGGINGFACE_API_TOKEN or HUGGINGFACE_API_KEY in Backend/.env"
        )

    model = os.environ.get('HUGGINGFACE_MODEL', 'Qwen/Qwen2.5-Coder-32B-Instruct')
    api_url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {hf_token}"}

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "top_p": 0.9,
    }

    for attempt in range(retries):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)

            # Handle "model is loading" (cold-start)
            if response.status_code == 503:
                if attempt < retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Model loading (cold-start), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return "Hugging Face model is loading. Try again in 30 seconds."

            # Handle quota/rate limit
            if response.status_code == 429:
                return "Hugging Face rate limit reached. Try again in a few moments."

            # Handle other HTTP errors
            if response.status_code != 200:
                error_msg = response.json().get('error', f'HTTP {response.status_code}')
                return f"Hugging Face API error: {error_msg}"

            # Parse response
            result = response.json()
            choices = result.get('choices', []) if isinstance(result, dict) else []
            if choices:
                text = choices[0].get('message', {}).get('content', '').strip()
                return text if text else "Empty response from Hugging Face."

            return "Unable to parse Hugging Face response."

        except requests.Timeout:
            if attempt < retries - 1:
                continue
            return "Request timeout. Hugging Face API not responding."
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                wait_time = backoff_factor ** attempt
                time.sleep(wait_time)
                continue
            return f"Error communicating with Hugging Face: {str(e)}"

    return "Failed after all retries."
