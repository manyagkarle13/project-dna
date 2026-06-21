"""
GitHub PR creation and PR review endpoints.
"""
import json
import re
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from auth_app.models import Repository
from repos.github_api import GitHubAPI
from repos import github_write
from core.llm import generate_ai_response


def generate_grounded_fix(file_path, file_content, description):
    prompt = f"""You are applying a precise bug fix to a source file in a repository.
    
We need you to generate the COMPLETE corrected contents of the file.
Base your modifications strictly on the provided file content and the fix request.
Do not use placeholders. Do not omit any code. Do not fabricate functions or imports.
If the requested fix cannot be resolved from this file, or if the request is invalid, return exactly: NO_SAFE_FIX

FILE PATH: {file_path}
FIX REQUEST: {description}

CURRENT FILE CONTENT:
{file_content}

Return ONLY the corrected code in a markdown code block (e.g. ```python ... ```). Do not add any text before or after the code block.
"""
    try:
        response = generate_ai_response(prompt, max_tokens=min(3000, max(800, len(file_content) // 2)))
        if response.strip() == 'NO_SAFE_FIX' or response.startswith(('ERROR:', 'AI service error:', 'Request timeout')):
            return None
        match = re.search(r'```(?:[\w.+-]+)?\s*\n?(.*?)```', response, flags=re.DOTALL)
        candidate = match.group(1).strip() if match else response.strip()
        return candidate if candidate and candidate != file_content.strip() else None
    except Exception:
        return None


def generate_summary_of_change(description):
    prompt = f"Summarize the following code change request in one short sentence: {description}"
    try:
        summary = generate_ai_response(prompt, max_tokens=50).strip()
        return summary
    except Exception:
        return f"Applied fix for: {description}"


@csrf_exempt
@require_http_methods(["POST"])
def api_review_pull_request(request, repo_id):
    """
    Review a pull request on a connected repository.
    POST /api/repos/{repo_id}/review-pr/
    Body: {pr_number: int}
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    pr_number = data.get('pr_number')
    if not pr_number:
        return JsonResponse({'error': 'pr_number required'}, status=400)

    repo = Repository.objects.filter(id=repo_id, user=request.user).first()
    if not repo:
        return JsonResponse({'error': 'Repository not found'}, status=404)

    # Safety boundary validation
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.has_full_agent_access or repo.source != 'github_owned':
        return JsonResponse({'error': 'Pull-request review is denied for this repository.'}, status=403)

    if not profile.github_token:
        return JsonResponse({'error': 'GitHub access not linked'}, status=403)

    try:
        owner, repo_name = repo.full_name.split('/')
        github = GitHubAPI(profile.github_token)

        # Fetch PR files patches (diff)
        url = f"{github.BASE_URL}/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
        response = requests.get(url, headers=github.headers)
        if response.status_code != 200:
            return JsonResponse({'error': f'Could not fetch PR files: {response.text}'}, status=response.status_code)

        pr_files = response.json()
        if not pr_files:
            return JsonResponse({'error': 'No files found in PR'}, status=400)

        # Build diff for AI review
        diff_parts = []
        for f in pr_files:
            filename = f.get('filename')
            patch = f.get('patch', '')
            diff_parts.append(f"File: {filename}\n{patch}\n")
        diff_content = "\n".join(diff_parts)

        if not diff_content.strip():
            return JsonResponse({'error': 'PR Diff is empty'}, status=400)

        # Get AI review
        review_prompt = f"""Review this GitHub pull request diff and identify:
1. Code quality issues
2. Potential bugs or security risks
3. Performance concerns
4. Best practice violations

PR Diff:
{diff_content[:12000]}

FORMAT YOUR RESPONSE USING MARKDOWN:
- Use proper line breaks between sections
- Use headers (## ###) for different categories (Quality Issues, Security Risks, etc.)
- Use **bold** for emphasis and `code` for code references
- Use bullet points to list findings
- Never return a single dense paragraph
- Be specific with file paths and line numbers when possible

Provide a concise, actionable review."""

        review_text = generate_ai_response(review_prompt, max_tokens=1000)

        return JsonResponse({
            'pr_number': pr_number,
            'files_changed': len(pr_files),
            'review': review_text
        })

    except Exception as e:
        print(f"Error reviewing PR: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_apply_fix_and_open_pr(request, repo_id):
    """
    Apply a fix to code and open a pull request.
    POST /api/repos/{repo_id}/apply-fix/
    Body: {file_path: str, description: str}
    Requires: has_full_agent_access (GitHub-linked user), repo.source == 'github_owned'
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    repo = Repository.objects.filter(id=repo_id, user=request.user).first()
    if not repo:
        return JsonResponse({'error': 'Repository not found'}, status=404)

    # Safety boundary checks
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.has_full_agent_access or repo.source != 'github_owned':
        return JsonResponse({'error': 'Pull-request creation is denied for this repository.'}, status=403)

    if not profile.github_token:
        return JsonResponse({'error': 'GitHub token not linked'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    file_path = data.get('file_path')
    description = data.get('description', '').strip()

    if not file_path or not description:
        return JsonResponse({'error': 'file_path and description are required'}, status=400)

    from repos.services import resolve_repo_file_path
    file_path = resolve_repo_file_path(repo, file_path)

    try:
        owner, repo_name = repo.full_name.split('/')
        github = GitHubAPI(profile.github_token)

        # 1. Fetch file content from repository
        file_data = github.get_file_content(owner, repo_name, file_path, repo.default_branch)
        if not file_data:
            return JsonResponse({'error': f'Could not read file {file_path} from GitHub'}, status=400)

        original_content = file_data['content']

        # 2. Call LLM to generate corrected content (grounded in the original file content + fix request description)
        fixed_content = generate_grounded_fix(file_path, original_content, description)
        if not fixed_content:
            return JsonResponse({'error': 'No safe complete-file fix could be generated. Grounded fix generation failed.'}, status=422)

        # 3. Call github_write orchestration to apply fix and open PR
        result = github_write.apply_fix_and_open_pr(repo, request.user, file_path, fixed_content, description)

        # 4. Generate summary of change
        summary_of_change = generate_summary_of_change(description)

        return JsonResponse({
            'pr_url': result['pr_url'],
            'pr_number': result['pr_number'],
            'branch_name': result['branch_name'],
            'summary_of_change': summary_of_change
        }, status=201)

    except Exception as e:
        print(f"Error creating PR: {e}")
        return JsonResponse({'error': str(e)}, status=500)
