import requests
import os
from django.conf import settings
from vectormemory.services import search_relevant_chunks
from chat.static_analysis import run_static_analysis

def generate_agent_response(conversation, user_message):
    """
    Generate AI response using FREE Ollama (local AI model)

    Completely free, no quotas, works offline!
    Runs on your computer locally.

    Setup:
    1. Download Ollama from https://ollama.ai/
    2. Run: ollama run llama2
    3. Add to Backend/.env: OLLAMA_API_URL=http://localhost:11434
    4. Restart backend
    """

    ollama_url = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434')

    try:
        # Check if Ollama is running
        check_response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if check_response.status_code != 200:
            return """Ollama is not running!

To use FREE local AI:
1. Download Ollama: https://ollama.ai/
2. Install and open Ollama
3. Run in terminal: ollama run llama2
4. Add to Backend/.env: OLLAMA_API_URL=http://localhost:11434
5. Restart this backend

Ollama gives you:
- Completely FREE AI
- No quotas ever
- Works offline
- No API key needed
- Runs on your computer"""

        # Build prompt
        history = conversation.messages.order_by('-created_at')[:10]
        history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in reversed(history)])

        prompt = f"Conversation History:\n{history_text}\n\n"

        if conversation.repo:
            prompt += f"Project Summary:\n{conversation.repo.ai_summary}\n\n"
            chunks = search_relevant_chunks(conversation.repo, user_message, top_k=5)

            if not chunks:
                prompt += "No relevant code found in repository. Answer based on general knowledge.\n\n"
            else:
                prompt += "Relevant Code Chunks:\n\n"
                bug_keywords = ["bug", "error", "fix", "broken", "issue", "crash", "fails", "exception", "vulnerability", "security"]
                check_bugs = any(kw in user_message.lower() for kw in bug_keywords)

                for chunk in chunks:
                    prompt += f"--- {chunk.file_path} (Chunk {chunk.chunk_index}) ---\n{chunk.content}\n\n"

                    if check_bugs:
                        findings = run_static_analysis(chunk.file_path, chunk.content)
                        if findings:
                            prompt += f"--- Static Analysis Findings for {chunk.file_path} ---\n"
                            for finding in findings:
                                prompt += f"Line {finding['line']}: [{finding['severity'].upper()}] {finding['message']}\n"
                            prompt += "\n"

                prompt += """Based on the provided code chunks, identify root causes for bugs, reference specific file paths/line numbers, and suggest concrete fixes.
Format fixes as:
FILE: path/to/file
CHANGE: describe the change
CODE: provide the fixed code snippet"""
        else:
            prompt += "You are a helpful coding assistant.\n\n"

        prompt += f"User: {user_message}\nAssistant:"

        # Call Ollama API
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'Unable to generate response').strip()
        else:
            return f"Ollama error: {response.status_code}\n\nMake sure ollama is running: ollama run llama2"

    except requests.exceptions.ConnectionError:
        return """Ollama is not running!

To start using FREE local AI:
1. Download Ollama from https://ollama.ai/
2. Open Ollama app
3. Open terminal and run: ollama run llama2
4. Wait for it to load
5. Then this app will work!

First request takes 30 seconds to load the model.
After that, responses are faster."""

    except requests.exceptions.Timeout:
        return "Ollama is loading the model (first time takes ~30 seconds). Please try again!"

    except Exception as e:
        return f"Error connecting to local AI: {str(e)}\n\nMake sure Ollama is running with: ollama run llama2"
