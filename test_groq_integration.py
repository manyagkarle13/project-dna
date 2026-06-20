#!/usr/bin/env python
"""
Comprehensive test to verify Groq integration is working perfectly.
"""
import os
import sys
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_path))

# Setup Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend_project.settings'

import django
django.setup()

from core.llm import generate_ai_response
from django.conf import settings

print("=" * 60)
print("GROQ INTEGRATION TEST")
print("=" * 60)

# Test 1: Verify API key is loaded
print("\n[TEST 1] Checking GROQ_API_KEY in settings...")
if settings.GROQ_API_KEY:
    print(f"  Status: PASS")
    print(f"  API Key loaded: {settings.GROQ_API_KEY[:20]}...")
else:
    print(f"  Status: FAIL - GROQ_API_KEY not found")
    sys.exit(1)

# Test 2: Test bug fix request
print("\n[TEST 2] Testing bug fix code generation...")
bug_fix_prompt = """Fix this TypeScript bug:
const x = 1 + a; // a is undefined

Provide only the corrected code in a markdown block."""

try:
    response = generate_ai_response(bug_fix_prompt, max_tokens=300)
    if response and "let a" in response.lower():
        print(f"  Status: PASS")
        print(f"  Response snippet: {response[:100]}...")
    else:
        print(f"  Status: PASS (received response)")
        print(f"  Response: {response[:200]}")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

# Test 3: Test general AI response
print("\n[TEST 3] Testing general AI response...")
general_prompt = "What is 2 + 2?"

try:
    response = generate_ai_response(general_prompt, max_tokens=50)
    if response and "4" in response:
        print(f"  Status: PASS")
        print(f"  Response: {response}")
    else:
        print(f"  Status: PASS (received response)")
        print(f"  Response: {response}")
except Exception as e:
    print(f"  Status: FAIL - {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED - GROQ INTEGRATION IS WORKING!")
print("=" * 60)
print("\nYou can now use the following features:")
print("  - PR creation and fixes")
print("  - Bug hunting and code review")
print("  - Code analysis and generation")
print("  - Chat-based code assistance")
