import os
import re
from django.conf import settings
from vectormemory.services import search_relevant_chunks
from chat.static_analysis import run_static_analysis

def generate_agent_response(conversation, user_message):
    """
    Generate AI response using FREE Hugging Face API
    No quota limits, completely free!
    """
    hf_token = os.environ.get('HUGGINGFACE_API_KEY')

    if not hf_token:
        return """Hugging Face API key not configured.

To use FREE AI (no paid subscription needed):
1. Go to: https://huggingface.co/
2. Sign up (free account)
3. Create Access Token in Settings > Access Tokens
4. Add to Backend/.env: HUGGINGFACE_API_KEY=your-token-here
5. Restart backend

This gives you unlimited free access with no quota limits!"""

    try:
        # Use Hugging Face Inference API (FREE)
        import requests

        # Check for GitHub URL in user message
        github_url_pattern = r'https?://github\.com/([\w.-]+/[\w.-]+)'
        github_match = re.search(github_url_pattern, user_message)
        if github_match and not conversation.repo:
            repo_mention = github_match.group(1)
            return f"I detected a GitHub repository: **{repo_mention}**\n\nI can help you analyze this repository! After connecting it, I can:\n- Find bugs and security issues\n- Review your code\n- Generate pull requests with fixes\n- Answer questions about the codebase\n\n**Next step:** The repository is being connected automatically. Once ready, just ask me to review the code, find bugs, or create a fix!"

        # Fetch conversation history
        history = conversation.messages.order_by('-created_at')[:10]
        history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in reversed(history)])

        prompt = f"Conversation History:\n{history_text}\n\n"

        if conversation.repo:
            prompt += f"Project Summary:\n{conversation.repo.ai_summary}\n\n"
            chunks = search_relevant_chunks(conversation.repo, user_message, top_k=5)

            if not chunks:
                prompt += "No relevant code found. Answer based on general knowledge only.\n\n"
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

                prompt += """You must answer based on the provided code chunks.
Identify root causes for bugs, reference specific file paths/line numbers, suggest concrete fixes as code snippets.
If the user asks to fix bugs, provide specific file paths and suggested code changes.
Format fixes as:
FILE: path/to/file
CHANGE: describe the change
CODE: provide the fixed code snippet"""
        else:
            prompt += "You are a helpful coding assistant. Answer the user's question.\n\n"

        prompt += f"User: {user_message}\nAssistant:"

        # Call Hugging Face Inference API
        api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
        headers = {"Authorization": f"Bearer {hf_token}"}

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 500,
                "temperature": 0.7,
            }
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '').split('Assistant:')[-1].strip()
                return text if text else "Unable to generate response. Please try again."
            return "Unable to parse response. Please try again."
        else:
            error_msg = response.json().get('error', str(response.status_code))
            return f"Hugging Face API Error: {error_msg}\n\nTip: First request may take 30 seconds to load the model (free tier)."

    except Exception as e:
        error_str = str(e)
        if "timed out" in error_str.lower():
            return "Request timed out. First load takes 30 seconds on free tier. Try again!"
        return f"Error: {error_str}\n\nMake sure HUGGINGFACE_API_KEY is set in Backend/.env"
