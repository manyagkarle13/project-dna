import requests
import json
from datetime import datetime
import random
import string

class GitHubAPI:
    """GitHub API wrapper for creating branches, commits, and PRs"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token):
        """Initialize with GitHub personal access token"""
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def get_repo_details(self, owner, repo):
        """Get repository details"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def get_default_branch(self, owner, repo):
        """Get the default branch of a repository"""
        details = self.get_repo_details(owner, repo)
        if details:
            return details.get('default_branch', 'main')
        return 'main'

    def get_file_content(self, owner, repo, path, branch='main'):
        """Get file content and SHA from repo"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        params = {'ref': branch}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            import base64
            content = base64.b64decode(data.get('content', '')).decode('utf-8')
            return {
                'content': content,
                'sha': data.get('sha'),
                'path': data.get('path')
            }
        return None

    def create_branch(self, owner, repo, branch_name, from_branch='main'):
        """Create a new branch from an existing branch"""
        # Get SHA of the branch to branch from
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/refs/heads/{from_branch}"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return {'success': False, 'error': 'Could not get base branch SHA'}

        base_sha = response.json().get('object', {}).get('sha')

        # Create new branch
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code == 201:
            return {'success': True, 'branch': branch_name}
        return {'success': False, 'error': response.json()}

    def commit_file(self, owner, repo, path, content, message, branch, sha=None):
        """Create or update a file in the repository"""
        import base64

        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"

        # If no SHA provided, try to get it
        if not sha:
            file_data = self.get_file_content(owner, repo, path, branch)
            if file_data:
                sha = file_data['sha']

        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch
        }

        if sha:
            data["sha"] = sha

        response = requests.put(url, headers=self.headers, json=data)

        if response.status_code in [200, 201]:
            return {'success': True, 'data': response.json()}
        return {'success': False, 'error': response.json()}

    def create_pull_request(self, owner, repo, title, body, head_branch, base_branch='main', draft=False):
        """Create a pull request

        Args:
            draft (bool): create PR as draft when True
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "draft": draft
        }

        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code == 201:
            pr_data = response.json()
            return {
                'success': True,
                'pr_number': pr_data.get('number'),
                'pr_url': pr_data.get('html_url'),
                'pr_id': pr_data.get('id')
            }
        return {'success': False, 'error': response.json()}

    def list_open_prs(self, owner, repo):
        """List open pull requests"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        params = {'state': 'open', 'per_page': 10}
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            return response.json()
        return []

    def get_commits(self, owner, repo, branch='main', per_page=5):
        """Get recent commits on a branch"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
        params = {'sha': branch, 'per_page': per_page}
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            return response.json()
        return []

    def get_diff(self, owner, repo, base_branch, head_branch):
        """Get diff between two branches"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/compare/{base_branch}...{head_branch}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        return None

    def get_pull_request_diff(self, owner, repo, pr_number):
        """Return the unified diff for a pull request, or an empty string on failure."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        try:
            response = requests.get(url, headers=headers, timeout=30)
            return response.text if response.status_code == 200 else ""
        except requests.RequestException:
            return ""

    def merge_pr(self, owner, repo, pr_number, commit_title, commit_message, merge_method='squash'):
        """Merge a pull request"""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        data = {
            "commit_title": commit_title,
            "commit_message": commit_message,
            "merge_method": merge_method
        }

        response = requests.put(url, headers=self.headers, json=data)

        if response.status_code == 200:
            return {'success': True, 'message': 'PR merged successfully'}
        return {'success': False, 'error': response.json()}


def generate_branch_name(fix_type='fix'):
    """Generate a unique branch name for fixes"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{fix_type}/dna-{timestamp}-{random_suffix}"
