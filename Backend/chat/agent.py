"""
Chat agent using Groq API (llama-3.1-8b-instant).
Handles conversations, code analysis, and bug hunting.
"""
from core.llm import generate_ai_response
from vectormemory.services import search_relevant_chunks
from chat.static_analysis import run_static_analysis


def generate_agent_response(conversation, user_message):
    """
    Generate AI response for chat messages.
    Integrates vector memory search, static analysis, and Groq LLM.
    """
    # Fetch last 10 messages for context
    history = conversation.messages.order_by('-created_at')[:10]
    history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in reversed(history)])

    prompt = f"Conversation History:\n{history_text}\n\n"

    if conversation.repo:
        prompt += f"Project Summary:\n{conversation.repo.ai_summary}\n\n"

        # Search for relevant code chunks
        chunks = search_relevant_chunks(conversation.repo, user_message, top_k=5)

        if not chunks:
            prompt += "No relevant code was found for this query. Answer based on the project summary.\n\n"
        else:
            prompt += "Relevant Code Chunks:\n\n"

            # Check if this is a bug/fix related query
            bug_keywords = ["bug", "error", "fix", "broken", "issue", "crash", "fails", "exception", "vulnerability", "security"]
            check_bugs = any(kw in user_message.lower() for kw in bug_keywords)

            for chunk in chunks:
                prompt += f"--- {chunk.file_path} (Chunk {chunk.chunk_index}) ---\n{chunk.content}\n\n"

                # Run static analysis on relevant chunks
                if check_bugs:
                    findings = run_static_analysis(chunk.file_path, chunk.content)
                    if findings:
                        prompt += f"--- Static Analysis for {chunk.file_path} ---\n"
                        for finding in findings:
                            prompt += f"Line {finding['line']}: [{finding['severity'].upper()}] {finding['message']}\n"
                        prompt += "\n"

            prompt += """You are an expert code analyst. Base your response ONLY on the provided code chunks and project summary.
If the user asks about code not shown, say 'I don't have that code in my analysis.'
If asked to find bugs, use the static analysis findings and provide specific fixes with file paths and line numbers.

FORMAT YOUR RESPONSE USING MARKDOWN:
- Use proper line breaks between distinct points and sections
- Always wrap code in triple-backtick code blocks with the correct language identifier (e.g. ```python, ```javascript, ```css)
- Use clear structure: short paragraphs, bullet points, or labeled sections
- Never return a single dense unbroken paragraph, especially when the response includes code
- Use headers (# ## ###) to organize sections
- Use **bold** for emphasis and `inline code` for variable/function names

Format fixes as:
```
FILE: path/to/file.py
LINE: [number]
ISSUE: description
FIX: [code block showing corrected code]
```
"""
    else:
        prompt += """You are a helpful coding assistant answering general questions.

FORMAT YOUR RESPONSE USING MARKDOWN:
- Use proper line breaks between distinct points and sections
- Always wrap code in triple-backtick code blocks with the correct language identifier (e.g. ```python, ```javascript, ```css)
- Use clear structure: short paragraphs, bullet points, or labeled sections
- Never return a single dense unbroken paragraph, especially when the response includes code
- Use headers (# ## ###) to organize sections
- Use **bold** for emphasis and `inline code` for variable/function names
"""

    prompt += f"User: {user_message}\nAssistant:"

    # Call Groq via shared LLM helper
    response = generate_ai_response(prompt, max_tokens=1000)
    return response

