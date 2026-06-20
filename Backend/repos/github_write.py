import base64
import time
import requests
from django.utils.text import slugify
from repos.github_api import GitHubAPI

def get_github_client(connected_repo):
    profile = getattr(connected_repo.user, 'profile', None)
    if not profile:
        profile = getattr(connected_repo.user, 'userprofile', None)
    token = profile.github_token if profile else None
    if not token:
        raise ValueError("GitHub access token not found for this user.")
    return GitHubAPI(token)

def create_branch(connected_repo, branch_name):
    """
    Fetches the SHA of the repo's default branch via GET /repos/{owner}/{repo}/git/refs/heads/{default_branch},
    then creates a new branch via POST /repos/{owner}/{repo}/git/refs pointing at that SHA.
    """
    owner, repo_name = connected_repo.full_name.split('/')
    default_branch = connected_repo.default_branch or 'main'
    
    github = get_github_client(connected_repo)
    
    # 1. Fetch SHA of default branch
    url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/git/refs/heads/{default_branch}"
    response = requests.get(url, headers=github.headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch SHA of default branch: {response.text}")
    
    sha = response.json().get('object', {}).get('sha')
    if not sha:
        raise Exception("Could not find object SHA in refs response.")
        
    # 2. Create new branch
    create_url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/git/refs"
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    response = requests.post(create_url, headers=github.headers, json=payload)
    if response.status_code != 201:
        raise Exception(f"Failed to create branch {branch_name}: {response.text}")
        
    return branch_name

def commit_file_change(connected_repo, branch_name, file_path, new_content, commit_message):
    """
    Fetches the current file's SHA via GET /repos/{owner}/{repo}/contents/{file_path}?ref={branch_name},
    then commits the change via PUT /repos/{owner}/{repo}/contents/{file_path} with base64-encoded content,
    commit message, and branch name.
    """
    owner, repo_name = connected_repo.full_name.split('/')
    github = get_github_client(connected_repo)
    
    # 1. Fetch current file's SHA on the new branch
    url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/contents/{file_path}"
    params = {'ref': branch_name}
    response = requests.get(url, headers=github.headers, params=params)
    
    sha = None
    if response.status_code == 200:
        sha = response.json().get('sha')
    elif response.status_code != 404:
        raise Exception(f"Failed to get file contents/SHA for {file_path}: {response.text}")
        
    # 2. Commit the change via PUT
    put_url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/contents/{file_path}"
    content_b64 = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": branch_name
    }
    if sha:
        payload["sha"] = sha
        
    response = requests.put(put_url, headers=github.headers, json=payload)
    if response.status_code not in (200, 201):
        raise Exception(f"Failed to commit file change to {file_path}: {response.text}")
        
    return response.json()

def open_pull_request(connected_repo, branch_name, title, description):
    """
    Opens a PR via POST /repos/{owner}/{repo}/pulls from branch_name to the repo's default branch.
    Returns the PR's URL and number.
    """
    owner, repo_name = connected_repo.full_name.split('/')
    default_branch = connected_repo.default_branch or 'main'
    github = get_github_client(connected_repo)
    
    url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/pulls"
    payload = {
        "title": title,
        "body": description,
        "head": branch_name,
        "base": default_branch
    }
    response = requests.post(url, headers=github.headers, json=payload)
    if response.status_code != 201:
        raise Exception(f"Failed to create pull request: {response.text}")
        
    data = response.json()
    return data.get('html_url'), data.get('number')

def apply_fix_and_open_pr(connected_repo, user, file_path, fixed_content, description):
    """
    Orchestrates branch creation, commit, and PR creation.
    Handles branch name collision retries once.
    Clean up branch if commit or PR creation fails.
    """
    owner, repo_name = connected_repo.full_name.split('/')
    short_slug = slugify(file_path.split('/')[-1])[:20] or "fix"
    
    # helper to generate branch name pattern: dna-fix/<short-slug>-<unix-timestamp>
    def make_branch_name():
        return f"dna-fix/{short_slug}-{int(time.time())}"
        
    branch_name = make_branch_name()
    
    try:
        try:
            create_branch(connected_repo, branch_name)
        except Exception as e:
            # Retry once with a fresh timestamp after a short delay to ensure unique timestamp
            time.sleep(1.1)
            branch_name = make_branch_name()
            create_branch(connected_repo, branch_name)
    except Exception as e:
        raise Exception(f"Branch creation failed: {str(e)}")
        
    # We created the branch successfully. Now commit the change
    commit_msg = f"dna-fix: apply bug fix to {file_path}"
    try:
        commit_file_change(connected_repo, branch_name, file_path, fixed_content, commit_msg)
    except Exception as e:
        # Cleanup: delete the created branch if possible
        github = get_github_client(connected_repo)
        delete_url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/git/refs/heads/{branch_name}"
        requests.delete(delete_url, headers=github.headers)
        raise Exception(f"File commit failed: {str(e)}")
        
    # Now open the PR
    pr_title = f"Fix: {description[:50]}"
    pr_body = f"""### Project DNA Bug Fix
    
Applied an automated fix for `{file_path}` based on:
> {description}

Please review these changes before merging.
"""
    try:
        pr_url, pr_number = open_pull_request(connected_repo, branch_name, pr_title, pr_body)
    except Exception as e:
        # Cleanup: delete the created branch if possible
        github = get_github_client(connected_repo)
        delete_url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/git/refs/heads/{branch_name}"
        requests.delete(delete_url, headers=github.headers)
        raise Exception(f"PR creation failed: {str(e)}")
        
    return {
        'pr_url': pr_url,
        'pr_number': pr_number,
        'branch_name': branch_name
    }
