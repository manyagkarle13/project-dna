#!/usr/bin/env python3
"""
Project DNA - PR Creation & Auto-Fix Examples

This script demonstrates how to use the new PR creation and auto-fix features.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Example 1: Auto-fix bugs and create PR
def auto_fix_bugs_and_create_pr(auth_token, repo_id):
    """
    Find bugs in a repository, generate fixes, and create a PR.
    """
    print("Example 1: Auto-fix bugs and create PR")
    print("=" * 50)

    url = f"{BASE_URL}/api/ai/bug-hunt/"

    payload = {
        "repo_id": repo_id,
        "auto_fix": True,
        "create_pr": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    print(f"\nStatus: {response.status_code}")
    print(f"PR Created: {result.get('pr_created', False)}")

    if result.get('pr_created'):
        print(f"PR Number: #{result['pr_number']}")
        print(f"PR URL: {result['pr_url']}")
        print(f"Fixes Applied: {len(result.get('fixes_applied', []))}")

    print(f"\nFindings ({len(result.get('findings', []))}):")
    for finding in result.get('findings', [])[:3]:
        print(f"  - [{finding['severity']}] {finding['issue']} in {finding['file']}")

    return result


# Example 2: Edit a file and create a PR
def edit_file_and_create_pr(auth_token, repo_id, file_path, new_content):
    """
    Edit a file in a repository and create a PR.
    """
    print("\nExample 2: Edit file and create PR")
    print("=" * 50)

    url = f"{BASE_URL}/api/repos/file/"

    payload = {
        "repo_id": repo_id,
        "file_path": file_path,
        "content": new_content,
        "commit_message": f"Update {file_path}",
        "create_pr": True,
        "pr_title": f"Update: {file_path}",
        "pr_body": f"This PR updates {file_path} with improvements."
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    print(f"\nStatus: {response.status_code}")
    print(f"Success: {result.get('success', False)}")

    if result.get('pr_created'):
        print(f"PR Number: #{result['pr_number']}")
        print(f"PR URL: {result['pr_url']}")
        print(f"Branch: {result['branch']}")

    return result


# Example 3: Create PR with multiple file fixes
def create_pr_with_multiple_fixes(auth_token, repo_id, fixes):
    """
    Create a PR with multiple file fixes.

    fixes = [
        {
            "path": "file1.js",
            "content": "new content",
            "description": "Fix security issue"
        },
        {
            "path": "file2.js",
            "content": "new content",
            "description": "Update API call"
        }
    ]
    """
    print("\nExample 3: Create PR with multiple fixes")
    print("=" * 50)

    url = f"{BASE_URL}/api/repos/create-pr-fix/"

    payload = {
        "repo_id": repo_id,
        "bug_description": "Multiple security and performance fixes",
        "files_to_fix": fixes
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    print(f"\nStatus: {response.status_code}")
    print(f"Success: {result.get('success', False)}")

    if result.get('pr_created'):
        print(f"PR Number: #{result['pr_number']}")
        print(f"PR URL: {result['pr_url']}")
        print(f"Branch: {result['branch']}")
        print(f"Files Committed: {len(result.get('commits', []))}")

    return result


# Example 4: Read a file from repository
def read_file_from_repo(auth_token, repo_id, file_path):
    """
    Read a file from a connected repository.
    """
    print("\nExample 4: Read file from repository")
    print("=" * 50)

    url = f"{BASE_URL}/api/repos/file/"
    params = {
        "repo_id": repo_id,
        "file_path": file_path
    }

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.get(url, params=params, headers=headers)
    result = response.json()

    print(f"\nStatus: {response.status_code}")
    print(f"File: {result.get('file_path')}")

    if 'content' in result:
        content = result['content']
        print(f"Content length: {len(content)} chars")
        print(f"First 200 chars:\n{content[:200]}...")

    return result


# Main execution
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PROJECT DNA - PR CREATION & AUTO-FIX EXAMPLES")
    print("=" * 70)

    # Configuration
    AUTH_TOKEN = "your-auth-token-here"  # Get this from login
    REPO_ID = 1  # Your repository ID

    print(f"\nBase URL: {BASE_URL}")
    print(f"Repository ID: {REPO_ID}")
    print(f"Auth Token: {AUTH_TOKEN[:20]}...")

    print("\n" + "=" * 70)
    print("USAGE INSTRUCTIONS")
    print("=" * 70)

    print("""
1. Get Authentication Token:
   - Sign in to Project DNA
   - The token is in localStorage or session

2. Get Repository ID:
   - Connect a repository
   - The ID is in the response or database

3. Run Examples:
   - python3 pr_examples.py
   - Update AUTH_TOKEN and REPO_ID

4. Check Results:
   - Look for PR links in output
   - Visit GitHub to see created PRs
   - Review and merge PRs

5. Advanced Usage:
   - Edit files before creating PR
   - Batch multiple fixes
   - Run auto-fix after bug hunt
   - Create PR with custom title/body
    """)

    print("\n" + "=" * 70)
    print("EXAMPLE COMMANDS")
    print("=" * 70)

    # Example usage (commented out, requires valid credentials)
    """
    # Find bugs and auto-fix with PR
    result = auto_fix_bugs_and_create_pr(AUTH_TOKEN, REPO_ID)

    # Edit a file and create PR
    new_content = "console.log('Updated code');"
    result = edit_file_and_create_pr(
        AUTH_TOKEN, REPO_ID, "src/app.js", new_content
    )

    # Create PR with multiple fixes
    fixes = [
        {
            "path": "src/app.js",
            "content": "...",
            "description": "Fix XSS vulnerability"
        }
    ]
    result = create_pr_with_multiple_fixes(AUTH_TOKEN, REPO_ID, fixes)

    # Read a file
    result = read_file_from_repo(AUTH_TOKEN, REPO_ID, "src/app.js")
    """

    print("\nTo run these examples, uncomment the function calls above and")
    print("provide valid AUTH_TOKEN and REPO_ID values.")
    print("\n" + "=" * 70)
