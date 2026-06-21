#!/usr/bin/env python
"""
Test script to verify Groq LLM integration is working.
"""
import os
from dotenv import load_dotenv
from groq import Groq

if __name__ == "__main__":
    load_dotenv()

    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not found in .env")
        exit(1)

    print("Testing Groq API...")
    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Fix the bug in this TypeScript code: const x = 1 + a; // a is undefined"}],
            max_tokens=200,
            temperature=0.3,
        )
        result = response.choices[0].message.content
        print(f"\nGroq API Response:\n{result}")
        print("\n[SUCCESS] Groq integration working!")
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
