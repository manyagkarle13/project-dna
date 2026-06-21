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

            # Limit total characters added by chunks to prevent exceeding rate limits (max ~12,000 chars for chunks)
            MAX_CHUNKS_CHARS = 12000
            chunks_added_chars = 0

            for chunk in chunks:
                chunk_header = f"--- {chunk.file_path} (Chunk {chunk.chunk_index}) ---\n"
                chunk_body = chunk.content
                
                # Check if we have budget left
                if chunks_added_chars >= MAX_CHUNKS_CHARS:
                    break
                    
                # If adding the whole chunk exceeds the budget, truncate it
                if chunks_added_chars + len(chunk_header) + len(chunk_body) > MAX_CHUNKS_CHARS:
                    allowed_body_len = MAX_CHUNKS_CHARS - chunks_added_chars - len(chunk_header) - 50
                    if allowed_body_len > 100:
                        chunk_body = chunk_body[:allowed_body_len] + "\n... [TRUNCATED DUE TO SIZE LIMIT] ..."
                    else:
                        break
                
                chunk_text = f"{chunk_header}{chunk_body}\n\n"
                prompt += chunk_text
                chunks_added_chars += len(chunk_text)

                # Run static analysis on relevant chunks
                if check_bugs:
                    findings = run_static_analysis(chunk.file_path, chunk.content)
                    if findings:
                        findings_text = f"--- Static Analysis for {chunk.file_path} ---\n"
                        for finding in findings:
                            findings_text += f"Line {finding['line']}: [{finding['severity'].upper()}] {finding['message']}\n"
                        findings_text += "\n"
                        
                        # Only add if it fits the budget
                        if chunks_added_chars + len(findings_text) <= MAX_CHUNKS_CHARS:
                            prompt += findings_text
                            chunks_added_chars += len(findings_text)

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

