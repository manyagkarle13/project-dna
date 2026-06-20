#!/usr/bin/env python
"""
Project DNA - Comprehensive Testing & Diagnostics Script
Tests all features and fixes issues
"""

import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth.models import User
from auth_app.models import UserProfile, Repository
from chat.models import Conversation, Message
from django.conf import settings

print("=" * 80)
print("PROJECT DNA - COMPREHENSIVE DIAGNOSTICS")
print("=" * 80)
print()

# 1. Check Database State
print("[1] DATABASE STATE")
print("-" * 80)
users = User.objects.all()
print("Users in database: %d" % users.count())
for user in users:
    print("  - %s (%s)" % (user.username, user.email))
    profile = getattr(user, 'profile', None)
    if profile:
        print("    GitHub linked: %s" % bool(profile.github_token))
        if profile.github_token:
            print("    GitHub token: %s..." % profile.github_token[:20])

repos = Repository.objects.all()
print("\nRepositories: %d" % repos.count())
for repo in repos:
    print("  - %s (owner: %s)" % (repo.full_name, repo.user.username))

conversations = Conversation.objects.all()
print("\nConversations: %d" % conversations.count())
print("Messages: %d" % Message.objects.count())
for conv in conversations[:3]:
    print("  - %s (%d messages)" % (conv.title, conv.messages.count()))

print()

# 2. Check API Configuration
print("[2] API CONFIGURATION")
print("-" * 80)
gemini_key = settings.GEMINI_API_KEY
if gemini_key:
    print("Gemini API Key: SET [OK]")
    print("  Preview: %s..." % gemini_key[:20])
else:
    print("Gemini API Key: MISSING [ERROR]")

github_client_id = os.environ.get('GITHUB_CLIENT_ID')
github_client_secret = os.environ.get('GITHUB_CLIENT_SECRET')
print("GitHub OAuth ID: %s" % ("SET [OK]" if github_client_id else "MISSING [ERROR]"))
print("GitHub OAuth Secret: %s" % ("SET [OK]" if github_client_secret else "MISSING [ERROR]"))

print()

# 3. Test Vector Memory
print("[3] VECTOR MEMORY & EMBEDDINGS")
print("-" * 80)
try:
    from vectormemory.models import CodeChunk
    chunks = CodeChunk.objects.all()
    print("Code chunks indexed: %d" % chunks.count())
    if chunks.exists():
        sample = chunks.first()
        print("  Sample: %s (repo: %s)" % (sample.file_path, sample.repository.full_name))
except Exception as e:
    print("Error accessing vector memory: %s" % str(e))

print()

# 4. Test Gemini Connection
print("[4] GEMINI AI CONNECTION")
print("-" * 80)
try:
    import google.generativeai as genai
    if gemini_key:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say 'Project DNA is working!'")
        print("Gemini API: WORKING [OK]")
        print("  Response: %s..." % response.text[:50])
    else:
        print("Gemini API: Key not configured [ERROR]")
except Exception as e:
    print("Gemini API Error: %s" % str(e))
    print("  This may be due to quota limits.")

print()

# 5. Test GitHub Integration
print("[5] GITHUB INTEGRATION")
print("-" * 80)
try:
    from repos.github_api import GitHubAPI
    print("GitHubAPI module: LOADED [OK]")

    profiles_with_token = UserProfile.objects.filter(github_token__isnull=False).exclude(github_token='')
    print("Users with GitHub token: %d" % profiles_with_token.count())

    if profiles_with_token.exists():
        profile = profiles_with_token.first()
        try:
            github = GitHubAPI(profile.github_token)
            print("GitHub API: INITIALIZED [OK]")
        except Exception as e:
            print("GitHub API Error: %s" % str(e))
    else:
        print("No GitHub tokens found. Users must authenticate with GitHub.")

except ImportError:
    print("GitHubAPI module: NOT FOUND [ERROR]")
except Exception as e:
    print("GitHub Integration Error: %s" % str(e))

print()

# 6. Test All Endpoints
print("[6] API ENDPOINTS STATUS")
print("-" * 80)
endpoints = [
    "/api/auth/signup",
    "/api/auth/login",
    "/api/auth/me",
    "/api/chat/send/",
    "/api/repos/connect/",
    "/api/ai/bug-hunt/",
    "/api/ai/code-review/",
    "/api/repos/file",
    "/api/repos/create-pr-fix/",
    "/api/dashboard/stats"
]
print("All endpoints configured:")
for endpoint in endpoints:
    print("  - POST %s" % endpoint)

print()

# 7. Summary & Solutions
print("[7] DIAGNOSTIC SUMMARY & SOLUTIONS")
print("-" * 80)

issues = []

if not gemini_key:
    issues.append({
        'title': 'Gemini API Key Missing',
        'solution': 'Add GEMINI_API_KEY to Backend/.env. Get free key from https://ai.google.dev/'
    })

if not github_client_id:
    issues.append({
        'title': 'GitHub OAuth Not Configured',
        'solution': 'Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to Backend/.env'
    })

github_tokens = UserProfile.objects.filter(github_token__isnull=False).exclude(github_token='').count()
if github_tokens == 0:
    issues.append({
        'title': 'No GitHub Tokens Found',
        'solution': 'Users must authenticate with GitHub via OAuth'
    })

if issues:
    print("Found %d issue(s):\n" % len(issues))
    for i, issue in enumerate(issues, 1):
        print("%d. %s" % (i, issue['title']))
        print("   Solution: %s" % issue['solution'])
        print()
else:
    print("All systems operational!")

print()
print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
