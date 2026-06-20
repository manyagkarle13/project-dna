import os
import json
import re
import requests
import urllib.parse
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from auth_app.models import UserProfile, Repository
from chat.models import Conversation, Message
from core.llm import generate_ai_response
from vectormemory.services import search_relevant_chunks

PR_WRITE_FEATURE_MESSAGE = (
    "Repository write and pull-request creation are not enabled in this build. "
    "Project DNA can analyze code and suggest fixes in chat, but it will not write "
    "to a user's GitHub repository until the Phase 6 safety work is complete."
)

def friendly_ai_error(exc):
    raw = str(exc)
    lower = raw.lower()
    if "429" in raw or "quota" in lower or "rate limit" in lower or "resource_exhausted" in lower:
        return (
            "Hugging Face quota or rate limit was reached. Please wait a bit and try again."
        )
    if "api key" in lower or "permission" in lower or "unauthenticated" in lower:
        return "Hugging Face could not authenticate. Please check HUGGINGFACE_API_TOKEN in your backend .env."
    return "The AI provider could not complete this request. Please try again later."

# Helper to check credentials configuration
def has_google_creds():
    return bool(os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET'))

def has_github_creds():
    return bool(os.environ.get('GITHUB_CLIENT_ID') and os.environ.get('GITHUB_CLIENT_SECRET'))

# Signup view
@csrf_exempt
def api_signup(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not name or not email or not password:
        return JsonResponse({'error': 'Name, email, and password are required.'}, status=400)
        
    if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'An account with that email already exists.'}, status=400)
        
    try:
        # Create standard Django user, using email as the username
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = name
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Log the user in
        django_login(request, user)
        
        return JsonResponse({
            'user': {
                'id': user.id,
                'name': user.first_name,
                'email': user.email
            },
            'message': 'Signup successful!'
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error during user creation.'}, status=500)

# Login view
@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return JsonResponse({'error': 'Email and password are required.'}, status=400)
        
    # Authenticate user using email as username
    user = authenticate(request, username=email, password=password)
    if user is not None:
        django_login(request, user)
        return JsonResponse({
            'user': {
                'id': user.id,
                'name': user.first_name,
                'email': user.email
            },
            'message': 'Login successful!'
        })
    else:
        # Check if the user exists but has no password (signed up via Google/GitHub OAuth)
        if User.objects.filter(username=email).exists():
            usr = User.objects.get(username=email)
            if not usr.has_usable_password():
                return JsonResponse({
                    'error': 'This account uses social sign-in. Please sign in using Google or GitHub.'
                }, status=400)
        return JsonResponse({'error': 'Incorrect email or password.'}, status=400)

# Logout view
@csrf_exempt
def api_logout(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    django_logout(request)
    return JsonResponse({'message': 'Logout successful'})

# Get Current User Profile (Me)
def api_me(request):
    if request.user.is_authenticated:
        # Determine provider
        provider = 'local'
        github_username = None
        try:
            profile = request.user.profile
            if profile.github_id:
                provider = 'github'
                github_username = profile.github_username
            elif profile.google_id:
                provider = 'google'
        except UserProfile.DoesNotExist:
            pass

        return JsonResponse({
            'user': {
                'id': request.user.id,
                'name': request.user.first_name or request.user.username,
                'email': request.user.email,
                'auth_provider': provider,
                'github_username': github_username,
                'github_is_linked': bool(getattr(request.user, 'profile', None) and request.user.profile.github_token)
            }
        })
    else:
        return JsonResponse({'user': None})

# Health Check
def api_health(request):
    return JsonResponse({
        'status': 'healthy',
        'googleCredsSet': has_google_creds(),
        'githubCredsSet': has_github_creds(),
        'huggingFaceConfigured': bool(os.environ.get('HUGGINGFACE_API_TOKEN') or os.environ.get('HUGGINGFACE_API_KEY')),
    })

# =========================================================================
# OAUTH ENDPOINTS
# =========================================================================

# Google Auth Redirect
def auth_google(request):
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    if has_google_creds():
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        print("DEBUG: GOOGLE_CLIENT_ID in views is:", client_id)
        # Always use backend port for callback (Vite proxy uses frontend port as host)
        backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')
        callback_uri = f"{backend_url}/auth/google/callback"
        google_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={urllib.parse.quote(callback_uri)}&"
            "response_type=code&"
            "scope=openid%20email%20profile"
        )
        return HttpResponseRedirect(google_url)
    else:
        # Mock OAuth redirect
        return HttpResponseRedirect(f"/auth/mock?provider=google")

# Google Auth Callback
def auth_google_callback(request):
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    if not has_google_creds():
        return HttpResponseBadRequest("Google OAuth not configured on server.")
        
    code = request.GET.get('code')
    if not code:
        return HttpResponseRedirect(f"{frontend_url}?auth_error=google_no_code")
        
    try:
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        # Must match the redirect_uri used in the initial auth request
        backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')
        callback_uri = f"{backend_url}/auth/google/callback"
        
        # 1. Exchange authorization code for access token
        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": callback_uri,
                "grant_type": "authorization_code"
            }
        ).json()
        
        access_token = token_res.get('access_token')
        if not access_token:
            return HttpResponseRedirect(f"{frontend_url}?auth_error=google_token_exchange_failed")
            
        # 2. Fetch user information from Google API
        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name') or user_info.get('given_name', 'Google User')
        
        if not google_id:
            return HttpResponseRedirect(f"{frontend_url}?auth_error=google_profile_fetch_failed")
            
        # 3. Find or create user
        user = find_or_create_oauth_user(provider='google', provider_id=google_id, name=name, email=email)
        
        # 4. Login user session
        django_login(request, user)
        
        return HttpResponseRedirect(f"{frontend_url.rstrip('/')}/dashboard.html")
    except Exception as e:
        print("Google OAuth Exception:", e)
        return HttpResponseRedirect(f"{frontend_url}?auth_error=google_server_exception")

# GitHub Auth Redirect
def auth_github(request):
    if has_github_creds():
        client_id = os.environ.get('GITHUB_CLIENT_ID')
        # Always use backend port for callback (Vite proxy uses frontend port as host)
        backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')
        callback_uri = f"{backend_url}/auth/github/callback"
        github_url = (
            "https://github.com/login/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={urllib.parse.quote(callback_uri)}&"
            "scope=repo%20user:email"
        )
        return HttpResponseRedirect(github_url)
    else:
        # Mock OAuth redirect
        return HttpResponseRedirect(f"/auth/mock?provider=github")

# GitHub Link Redirect (for existing authenticated users)
def auth_github_link(request):
    if not request.user.is_authenticated:
        # Check token in query param just in case
        token = request.GET.get('token')
        if not token: # For simplicity, relying on Django session
            return HttpResponseRedirect(f"{os.environ.get('FRONTEND_URL', 'http://localhost:5173')}?auth_error=not_authenticated")

    if has_github_creds():
        client_id = os.environ.get('GITHUB_CLIENT_ID')
        backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8000')
        callback_uri = f"{backend_url}/auth/github/callback"
        # Attach state=link to differentiate from login
        github_url = (
            "https://github.com/login/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={urllib.parse.quote(callback_uri)}&"
            "scope=repo%20user:email&"
            "state=link"
        )
        return HttpResponseRedirect(github_url)
    else:
        return HttpResponseRedirect(f"/auth/mock?provider=github&state=link")

# GitHub Auth Callback
def auth_github_callback(request):
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    if not has_github_creds():
        return HttpResponseBadRequest("GitHub OAuth not configured on server.")
        
    code = request.GET.get('code')
    state = request.GET.get('state')
    is_linking = state == 'link'
    
    if not code:
        return HttpResponseRedirect(f"{frontend_url}?auth_error=github_no_code")
        
    try:
        client_id = os.environ.get('GITHUB_CLIENT_ID')
        client_secret = os.environ.get('GITHUB_CLIENT_SECRET')
        
        # 1. Exchange authorization code for access token
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret
            }
        ).json()
        
        access_token = token_res.get('access_token')
        if not access_token:
            return HttpResponseRedirect(f"{frontend_url}?auth_error=github_token_exchange_failed")
            
        # 2. Fetch user information from GitHub API
        user_res = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/json"
            }
        ).json()
        
        github_id = str(user_res.get('id'))
        name = user_res.get('name') or user_res.get('login') or 'GitHub User'
        email = user_res.get('email')
        
        # 3. If primary email is private/null, fetch emails list
        if not email:
            emails_res = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"}
            ).json()
            # Find primary verified email
            for email_entry in emails_res:
                if email_entry.get('primary') and email_entry.get('verified'):
                    email = email_entry.get('email')
                    break
            if not email and emails_res:
                email = emails_res[0].get('email')
                
        if not github_id:
            return HttpResponseRedirect(f"{frontend_url}?auth_error=github_profile_fetch_failed")
            
        # 4. Find or create user
        if is_linking:
            if not request.user.is_authenticated:
                return HttpResponseRedirect(f"{frontend_url.rstrip('/')}/dashboard.html?link_error=not_authenticated")
            user = request.user
            profile = user.profile
            profile.github_id = github_id
            profile.github_username = user_res.get('login')
            profile.github_token = access_token
            profile.save()
            return HttpResponseRedirect(f"{frontend_url.rstrip('/')}/dashboard.html?github_linked=true")
        else:
            user = find_or_create_oauth_user(provider='github', provider_id=github_id, name=name, email=email)

            # Save token and username in user profile
            try:
                profile = user.profile
                profile.github_username = user_res.get('login')
                profile.github_token = access_token
                profile.save()
            except Exception as e:
                print("Failed to save github token to profile:", e)
            
            # 5. Login user session
            django_login(request, user)
            
            return HttpResponseRedirect(f"{frontend_url.rstrip('/')}/dashboard.html")
    except Exception as e:
        print("GitHub OAuth Exception:", e)
        error_type = "github_link_exception" if is_linking else "github_server_exception"
        if is_linking:
            return HttpResponseRedirect(f"{frontend_url.rstrip('/')}/dashboard.html?link_error={error_type}")
        return HttpResponseRedirect(f"{frontend_url}?auth_error={error_type}")

# Mock Auth view
def auth_mock(request):
    provider = request.GET.get('provider', 'google')
    return render(request, 'mock-auth.html', {'provider': provider})

# Mock Auth callback
def auth_mock_callback(request):
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    provider = request.GET.get('provider')
    mock_id = request.GET.get('id')
    name = request.GET.get('name', 'Mock User')
    email = request.GET.get('email')
    
    if not provider or not mock_id:
        return HttpResponseBadRequest("Invalid mock auth callback parameters.")
        
    try:
        user = find_or_create_oauth_user(provider=provider, provider_id=mock_id, name=name, email=email)
        django_login(request, user)
        return HttpResponseRedirect(f"{frontend_url.rstrip('/')}/dashboard.html")
    except Exception as e:
        print("Mock Auth Callback Exception:", e)
        return HttpResponseRedirect(f"{frontend_url}?auth_error=mock_auth_failed")

# Helper function to find or create a user for social sign-ins
def find_or_create_oauth_user(provider, provider_id, name, email):
    # 1. Search UserProfile by provider identifier
    if provider == 'google':
        profile = UserProfile.objects.filter(google_id=provider_id).first()
    else:
        profile = UserProfile.objects.filter(github_id=provider_id).first()
        
    if profile:
        return profile.user
        
    # 2. Search by email to link account if email exists
    if email:
        user = User.objects.filter(email=email).first()
        if user:
            # Create user profile if missing
            profile, created = UserProfile.objects.get_or_create(user=user)
            if provider == 'google':
                profile.google_id = provider_id
            else:
                profile.github_id = provider_id
            profile.save()
            return user
            
    # 3. Create a brand new user
    username = email if email else f"{provider}_{provider_id}"
    
    # Ensure username is unique
    if User.objects.filter(username=username).exists():
        username = f"{username}_{User.objects.count()}"
        
    user = User.objects.create_user(username=username, email=email)
    user.first_name = name
    user.set_unusable_password() # Set unusable password for security
    user.save()
    
    # Create profile
    profile = UserProfile(user=user)
    if provider == 'google':
        profile.google_id = provider_id
    else:
        profile.github_id = provider_id
    profile.save()
    
    return user


# Serve frontend HTML files
def serve_index(request):
    return render(request, 'index.html')

def serve_dashboard(request):
    return render(request, 'dashboard.html')


# Get list of connected repositories
def api_repos_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    repos = Repository.objects.filter(user=request.user).order_by('-connected_at')
    repo_list = []
    for r in repos:
        repo_list.append({
            'id': r.id,
            'repo_url': r.repo_url,
            'full_name': r.full_name,
            'default_branch': r.default_branch,
            'tech_stack': r.tech_stack,
            'ai_summary': r.ai_summary,
            'file_tree': r.file_tree,
            'file_count': r.file_count,
            'total_size': r.total_size,
            'status': r.status,
            'error_message': r.error_message,
            'connected_at': r.connected_at.isoformat()
        })
    return JsonResponse({'repos': repo_list})


# Get user's available repositories from GitHub (fallback to mock list)
def api_github_repos_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    token = None
    try:
        token = request.user.profile.github_token
    except UserProfile.DoesNotExist:
        pass
        
    if token:
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            res = requests.get("https://api.github.com/user/repos?visibility=all&per_page=100&sort=updated", headers=headers)
            if res.status_code == 200:
                repos_data = res.json()
                formatted_repos = []
                for repo in repos_data:
                    updated_at_str = repo.get('updated_at', '')
                    formatted_repos.append({
                        "name": repo.get('name'),
                        "full_name": repo.get('full_name'),
                        "repo_url": repo.get('html_url'),
                        "language": repo.get('language') or 'Unknown',
                        "updated_at": updated_at_str,
                        "default_branch": repo.get('default_branch', 'main')
                    })
                return JsonResponse({'repos': formatted_repos})
            else:
                print("GitHub API Error:", res.text)
                return JsonResponse({'error': f'GitHub API Error: {res.text}'}, status=400)
        except Exception as e:
            print("Failed to fetch real github repos:", e)
            return JsonResponse({'error': f'Failed to fetch real github repos: {str(e)}'}, status=500)
            
    return JsonResponse({
        'error': 'GitHub is not linked. Link GitHub to browse private repositories, or paste a public repository URL.'
    }, status=403)


    # Connect a repository (mock cloning & analysis or save to DB)
@csrf_exempt
def api_repos_connect(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        
    repo_url = data.get('repo_url', '').strip()
    full_name = data.get('full_name', '').strip()
    default_branch = data.get('default_branch', 'main').strip()
    conversation_id = data.get('conversation_id')
    
    if not repo_url:
        return JsonResponse({'error': 'Repository URL is required.'}, status=400)

    from repos.services import normalize_github_repo_url
    try:
        repo_url, parsed_full_name = normalize_github_repo_url(repo_url)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    full_name = parsed_full_name
        
    # Link helper
    def link_repo_to_conv(repo, cid):
        if not cid:
            return
        conv = Conversation.objects.filter(id=cid, user=request.user).first()
        if conv:
            conv.repo = repo
            if conv.title == 'New Chat' or '...' in conv.title or conv.title == '':
                conv.title = f"Chat: {repo.full_name.split('/')[-1]}"
            conv.save()
            
            # System message
            ai_text = (
                f"I've successfully connected to **{repo.full_name}**.\n\n"
                f"**Detected Stack:** {', '.join(repo.tech_stack)}\n\n"
                f"{repo.ai_summary}"
            )
            # Avoid duplicate assistant messages in the same conversation
            if not conv.messages.filter(role='assistant', content__contains=f"I've successfully connected to **{repo.full_name}**").exists():
                Message.objects.create(conversation=conv, role='assistant', content=ai_text)
            
    existing = Repository.objects.filter(user=request.user, repo_url=repo_url).first()
    if existing:
        link_repo_to_conv(existing, conversation_id)
        return JsonResponse({
            'repo': {
                'id': existing.id,
                'repo_url': existing.repo_url,
                'full_name': existing.full_name,
                'default_branch': existing.default_branch,
                'tech_stack': existing.tech_stack,
                'ai_summary': existing.ai_summary,
                'file_tree': existing.file_tree,
                'file_count': existing.file_count,
                'total_size': existing.total_size,
                'connected_at': existing.connected_at.isoformat()
            },
            'message': 'Repository is already connected!'
        })
        
    from repos.services import process_new_repo
    from vectormemory.services import index_repo
    
    tech_stack = ["Auto-Detected"]
    
    repo = Repository.objects.create(
        user=request.user,
        repo_url=repo_url,
        full_name=full_name,
        default_branch=default_branch,
        tech_stack=tech_stack,
        status='processing'
    )
    
    try:
        processed = process_new_repo(repo_url)
    except ValueError as e:
        repo.status = "failed"
        repo.error_message = str(e)
        repo.save()
        return JsonResponse({'error': repo.error_message}, status=400)
    except Exception as e:
        print("Failed to process repo:", e)
        repo.status = "failed"
        repo.error_message = str(e)
        repo.save()
        return JsonResponse({'error': f'Failed to process repository: {str(e)}'}, status=500)
        
    try:
        repo.ai_summary = processed['ai_summary']
        repo.file_tree = processed['file_tree']
        repo.file_count = processed['file_count']
        repo.total_size = processed['total_size']
        repo.tech_stack = processed.get('tech_stack', ['Unknown/Other'])
        repo.status = processed.get('status', 'ready')
        repo.save()
        
        if processed['file_count'] > 0:
            index_repo(repo, processed['repo_path'])
            
        import shutil
        shutil.rmtree(processed['repo_path'], ignore_errors=True)
            
        link_repo_to_conv(repo, conversation_id)
        return JsonResponse({
            'repo': {
                'id': repo.id,
                'repo_url': repo.repo_url,
                'full_name': repo.full_name,
                'default_branch': repo.default_branch,
                'tech_stack': repo.tech_stack,
                'ai_summary': repo.ai_summary,
                'file_tree': repo.file_tree,
                'file_count': repo.file_count,
                'total_size': repo.total_size,
                'status': repo.status,
                'error_message': repo.error_message,
                'connected_at': repo.connected_at.isoformat()
            },
            'message': 'Repository connected successfully!'
        }, status=201)
    except Exception as e:
        import shutil
        if 'processed' in locals() and 'repo_path' in processed:
            shutil.rmtree(processed['repo_path'], ignore_errors=True)
            
        print("Failed to save connected repository:", e)
        repo.status = "failed"
        repo.error_message = 'Internal server error while saving repository.'
        repo.save()
        return JsonResponse({'error': repo.error_message}, status=500)

def generate_fixed_file_content(file_path, original_content, finding):
    """Ask the code model for one complete replacement file, never a partial diff."""
    prompt = f'''You are applying one precise bug fix to a source file.
Return the COMPLETE corrected contents of the file inside a single fenced code block with the correct language identifier.
Do not remove unrelated code. Do not use placeholders. If the issue is not real or cannot be safely fixed from this file, return exactly NO_SAFE_FIX.

FILE: {file_path}
REPORTED LINE: {finding.get('line', 'unknown')}
ISSUE: {finding.get('issue', '')}
SUGGESTED FIX: {finding.get('fix', '')}

CURRENT FILE:
{original_content}

Return ONLY the corrected code in a markdown code block (```language_identifier ... ```). Do not add explanation.
'''
    response = generate_ai_response(prompt, max_tokens=min(3000, max(800, len(original_content) // 2)))
    if response.strip() == 'NO_SAFE_FIX' or response.startswith(('ERROR:', 'Hugging Face API error:', 'Request timeout')):
        return None
    match = re.search(r'```(?:[\w.+-]+)?\s*\n?(.*?)```', response, flags=re.DOTALL)
    candidate = match.group(1).strip() if match else response.strip()
    return candidate if candidate and candidate != original_content.strip() else None


# Run AI Bug Hunt on a repository
@csrf_exempt
def api_ai_bug_hunt(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    repo_id = data.get('repo_id')
    auto_fix = data.get('auto_fix', False)
    create_pr = data.get('create_pr', False)

    if not repo_id:
        return JsonResponse({'error': 'repo_id is required.'}, status=400)

    repo = Repository.objects.filter(id=repo_id, user=request.user).first()
    if not repo:
        return JsonResponse({'error': 'Repository not found.'}, status=404)

    try:
        # Get code chunks for analysis
        chunks = list(search_relevant_chunks(repo, "bugs vulnerabilities errors issues", top_k=10))

        if not chunks:
            return JsonResponse({
                'repo_id': repo.id,
                'findings': [],
                'message': 'No code chunks found for analysis'
            })

        # Prepare code for analysis
        code_to_analyze = "\n\n".join([f"FILE: {c.file_path}\n{c.content}" for c in chunks[:5]])

        prompt = f"""Analyze the following code for bugs, vulnerabilities, and issues:

{code_to_analyze}

Return a JSON array with findings in a markdown code block. Each finding should have:
- file: filename
- line: approximate line number
- severity: "Critical", "High", "Medium", or "Low"
- issue: brief description
- fix: suggested code fix (if possible)

Format your response as:
```json
[{{"file": "...", "line": 1, "severity": "High", "issue": "...", "fix": "..."}}]
```

Only return the JSON in a code block, no other text."""

        try:
            response_text = generate_ai_response(prompt, max_tokens=1400)
            json_match = re.search(r'```(?:json)?\s*(.*?)```', response_text, flags=re.DOTALL | re.IGNORECASE)
            findings = json.loads((json_match.group(1) if json_match else response_text).strip())
            if not isinstance(findings, list):
                raise ValueError("Model response was not a JSON array.")
        except Exception:
            return JsonResponse({
                'repo_id': repo.id,
                'findings': [],
                'message': (
                    "Bug hunt could not produce verified structured findings. "
                    "No issues were reported because the AI response was not valid JSON."
                )
            }, status=502)

        response_data = {
            'repo_id': repo.id,
            'findings': findings,
            'message': f"Bug hunt completed. Found {len(findings)} issues.",
            'auto_fix_available': bool(getattr(getattr(request.user, 'profile', None), 'github_token', None))
        }

        if auto_fix:
            github_token = getattr(getattr(request.user, 'profile', None), 'github_token', None)
            if not github_token:
                return JsonResponse({
                    **response_data,
                    'error': 'Link GitHub before Project DNA can commit a fix or open a pull request.'
                }, status=403)

            from repos.github_api import GitHubAPI, generate_branch_name
            github = GitHubAPI(github_token)
            owner, repo_name = repo.full_name.split('/', 1)
            prepared_changes, skipped = [], []
            for finding in findings[:3]:
                file_path = finding.get('file')
                if not file_path:
                    skipped.append('A finding did not identify a file.')
                    continue
                file_data = github.get_file_content(owner, repo_name, file_path, repo.default_branch)
                if not file_data:
                    skipped.append(f'Could not read {file_path} from GitHub.')
                    continue
                if len(file_data['content']) > 60000:
                    skipped.append(f'{file_path} is too large for a safe automatic replacement.')
                    continue
                corrected_content = generate_fixed_file_content(file_path, file_data['content'], finding)
                if not corrected_content:
                    skipped.append(f'No safe complete-file fix was generated for {file_path}.')
                    continue
                prepared_changes.append((finding, file_data, corrected_content))

            if not prepared_changes:
                return JsonResponse({
                    **response_data,
                    'error': 'No safe automatic file changes were generated. Use the Repo Editor to apply the suggested fixes.',
                    'skipped': skipped
                }, status=422)

            branch_name = generate_branch_name('dna-bugfix')
            branch_result = github.create_branch(owner, repo_name, branch_name, repo.default_branch)
            if not branch_result['success']:
                return JsonResponse({**response_data, 'error': f"Could not create a fix branch: {branch_result.get('error')}"}, status=502)

            fixes_applied = []
            for finding, file_data, corrected_content in prepared_changes:
                result = github.commit_file(
                    owner, repo_name, file_data['path'], corrected_content,
                    f"Fix: {finding.get('issue', file_data['path'])[:120]}", branch_name, file_data['sha']
                )
                if result['success']:
                    fixes_applied.append(file_data['path'])
                else:
                    skipped.append(f"Could not commit {file_data['path']}.")

            if not fixes_applied:
                return JsonResponse({**response_data, 'error': 'No fixes could be committed.', 'branch': branch_name, 'skipped': skipped}, status=502)

            response_data.update({'fixes_applied': fixes_applied, 'branch': branch_name, 'skipped': skipped})
            if create_pr:
                pr_body = "## Project DNA bug fixes\n\n" + "\n".join(
                    f"- **{finding.get('severity', 'Unknown')}** `{finding.get('file')}`: {finding.get('issue')}"
                    for finding, _, _ in prepared_changes
                ) + "\n\nPlease review these AI-generated changes before merging."
                pr_result = github.create_pull_request(
                    owner, repo_name, f"Fix bugs found by Project DNA in {repo_name}", pr_body, branch_name, repo.default_branch
                )
                if not pr_result['success']:
                    return JsonResponse({**response_data, 'error': 'Fixes were committed, but the pull request could not be opened.', 'pr_error': pr_result.get('error')}, status=502)
                response_data.update({'pr_created': True, 'pr_number': pr_result['pr_number'], 'pr_url': pr_result['pr_url']})
            return JsonResponse(response_data)

        # If auto-fix requested and user has GitHub token
        if auto_fix and create_pr and len(findings) > 0:
            try:
                github_token = request.user.profile.github_token
                if github_token:
                    from repos.github_api import GitHubAPI, generate_branch_name

                    github = GitHubAPI(github_token)
                    owner, repo_name = repo.full_name.split('/')

                    # Create branch for fixes
                    branch_name = generate_branch_name('bugfix-auto')
                    github.create_branch(owner, repo_name, branch_name, repo.default_branch)

                    # Generate and apply fixes
                    fixes_applied = []
                    for finding in findings[:3]:  # Limit to first 3 fixes
                        if finding.get('fix') and finding.get('file'):
                            try:
                                # Get current file content
                                file_data = github.get_file_content(owner, repo_name, finding['file'], repo.default_branch)
                                if file_data:
                                    # Simple fix: replace issue location with fix
                                    fixed_content = file_data['content']

                                    # Commit fix
                                    result = github.commit_file(
                                        owner, repo_name, finding['file'],
                                        fixed_content, f"Fix: {finding['issue']}", branch_name,
                                        file_data['sha']
                                    )

                                    if result['success']:
                                        fixes_applied.append(finding['file'])
                            except:
                                pass

                    # Create PR with fixes
                    if fixes_applied:
                        pr_title = f"🐛 AI-Generated Bug Fixes - {repo_name}"
                        pr_body = f"""## Automated Bug Fixes

Found and fixed {len(findings)} issues in your codebase.

### Findings Fixed
{chr(10).join([f"- **{f['severity']}**: {f['issue']} in `{f['file']}`" for f in findings[:3]])}

---
*Created by Project DNA AI Code Agent*
*Please review the changes before merging*
"""
                        pr_result = github.create_pull_request(
                            owner, repo_name, pr_title, pr_body,
                            branch_name, repo.default_branch
                        )

                        if pr_result['success']:
                            response_data['pr_created'] = True
                            response_data['pr_number'] = pr_result['pr_number']
                            response_data['pr_url'] = pr_result['pr_url']
                            response_data['fixes_applied'] = fixes_applied
            except:
                pass

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': friendly_ai_error(e),
            'repo_id': repo_id
        }, status=500)

# Read or Write a file from the repository (Repo Editor feature)
@csrf_exempt
def api_repo_file(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'GET':
        repo_id = request.GET.get('repo_id')
        file_path = request.GET.get('file_path')

        if not repo_id or not file_path:
            return JsonResponse({'error': 'repo_id and file_path are required.'}, status=400)

        repo = Repository.objects.filter(id=repo_id, user=request.user).first()
        if not repo:
            return JsonResponse({'error': 'Repository not found.'}, status=404)

        # Try fetching from GitHub raw content
        try:
            branch = repo.default_branch or 'main'
            raw_url = f"https://raw.githubusercontent.com/{repo.full_name}/{branch}/{file_path}"
            res = requests.get(raw_url)

            if res.status_code == 200:
                content = res.text
            else:
                return JsonResponse({
                    'error': 'Could not fetch this file from the repository. No mock content was returned.'
                }, status=404)

            return JsonResponse({
                'repo_id': repo.id,
                'file_path': file_path,
                'content': content
            })
        except Exception as e:
            return JsonResponse({'error': f'Failed to read file: {str(e)}'}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

        repo_id = data.get('repo_id')
        file_path = data.get('file_path')
        content = data.get('content')
        commit_message = data.get('commit_message', f'Update {file_path}')
        branch = data.get('branch', 'main')
        create_pr = data.get('create_pr', False)

        if not all([repo_id, file_path, content]):
            return JsonResponse({'error': 'repo_id, file_path, and content are required.'}, status=400)

        repo = Repository.objects.filter(id=repo_id, user=request.user).first()
        if not repo:
            return JsonResponse({'error': 'Repository not found.'}, status=404)

        # Check if user has GitHub token
        try:
            github_token = request.user.profile.github_token
            if not github_token:
                return JsonResponse({
                    'error': 'GitHub token not found. Please link your GitHub account.'
                }, status=403)
        except:
            return JsonResponse({'error': 'GitHub account not linked.'}, status=403)

        try:
            from repos.github_api import GitHubAPI, generate_branch_name
            from repos.build_system import BuildSystem
            import tempfile
            import shutil

            github = GitHubAPI(github_token)
            owner, repo_name = repo.full_name.split('/')

            # If creating PR, use a new branch
            if create_pr:
                new_branch = generate_branch_name('fix')
                result = github.create_branch(owner, repo_name, new_branch, repo.default_branch)
                if not result['success']:
                    return JsonResponse({
                        'error': f"Failed to create branch: {result.get('error')}"
                    }, status=400)
                target_branch = new_branch
            else:
                target_branch = branch

            # Commit the file
            commit_result = github.commit_file(
                owner, repo_name, file_path, content,
                commit_message, target_branch
            )

            if not commit_result['success']:
                return JsonResponse({
                    'error': f"Failed to commit: {commit_result.get('error')}"
                }, status=400)

            response_data = {
                'success': True,
                'message': f'Successfully committed "{commit_message}" to {file_path}.',
                'file_path': file_path,
                'commit_hash': commit_result['data'].get('commit', {}).get('sha'),
                'branch': target_branch
            }

            # If creating PR, create it now
            if create_pr:
                pr_title = data.get('pr_title', f'Fix: {file_path}')
                pr_body = data.get('pr_body', f'Automated fix for {file_path}\n\n{commit_message}')

                pr_result = github.create_pull_request(
                    owner, repo_name, pr_title, pr_body,
                    target_branch, repo.default_branch
                )

                if pr_result['success']:
                    response_data['pr_created'] = True
                    response_data['pr_number'] = pr_result['pr_number']
                    response_data['pr_url'] = pr_result['pr_url']
                else:
                    response_data['pr_error'] = pr_result['error']

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'error': f'Failed to commit file: {str(e)}'
            }, status=500)

    return JsonResponse({'error': 'Method not allowed.'}, status=405)

# Create a PR with bug fixes
@csrf_exempt
def api_create_pr_with_fix(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    repo_id = data.get('repo_id')
    bug_description = data.get('bug_description', 'Fix issues in codebase')
    files_to_fix = data.get('files_to_fix', [])  # List of {path, fix}

    if not repo_id:
        return JsonResponse({'error': 'repo_id is required.'}, status=400)

    repo = Repository.objects.filter(id=repo_id, user=request.user).first()
    if not repo:
        return JsonResponse({'error': 'Repository not found.'}, status=404)

    # Check GitHub token
    try:
        github_token = request.user.profile.github_token
        if not github_token:
            return JsonResponse({
                'error': 'GitHub token not found. Please link your GitHub account.'
            }, status=403)
    except:
        return JsonResponse({'error': 'GitHub account not linked.'}, status=403)

    try:
        from repos.github_api import GitHubAPI, generate_branch_name

        github = GitHubAPI(github_token)
        owner, repo_name = repo.full_name.split('/')

        # Create feature branch
        branch_name = generate_branch_name('bugfix')
        result = github.create_branch(owner, repo_name, branch_name, repo.default_branch)

        if not result['success']:
            return JsonResponse({
                'error': f"Failed to create branch: {result.get('error')}"
            }, status=400)

        # Commit fixes to each file
        commits = []
        for file_fix in files_to_fix:
            file_path = file_fix.get('path')
            fix_content = file_fix.get('content')

            if not file_path or not fix_content:
                continue

            commit_result = github.commit_file(
                owner, repo_name, file_path, fix_content,
                f"Fix: {file_fix.get('description', file_path)}", branch_name
            )

            if commit_result['success']:
                commits.append({
                    'file': file_path,
                    'success': True,
                    'sha': commit_result['data'].get('commit', {}).get('sha')
                })
            else:
                commits.append({
                    'file': file_path,
                    'success': False,
                    'error': commit_result.get('error')
                })

        # Create PR
        pr_title = f"🐛 Automated Bug Fixes - {repo.full_name.split('/')[-1]}"
        pr_body = f"""## Automated Bug Fixes

**Description:** {bug_description}

### Files Changed
{chr(10).join([f"- `{file_fix.get('path')}`: {file_fix.get('description', 'Fix')}" for file_fix in files_to_fix])}

---
*Created by Project DNA AI Code Agent*
"""

        pr_result = github.create_pull_request(
            owner, repo_name, pr_title, pr_body,
            branch_name, repo.default_branch
        )

        if pr_result['success']:
            return JsonResponse({
                'success': True,
                'pr_created': True,
                'pr_number': pr_result['pr_number'],
                'pr_url': pr_result['pr_url'],
                'branch': branch_name,
                'commits': commits,
                'message': f'Created PR #{pr_result["pr_number"]} with bug fixes'
            })
        else:
            return JsonResponse({
                'success': False,
                'commits': commits,
                'pr_error': pr_result['error'],
                'message': 'Committed fixes but failed to create PR'
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'error': f'Failed to create PR with fixes: {str(e)}'
        }, status=500)

# Generate an AI Code Review for open PRs
@csrf_exempt
def api_ai_code_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        
    repo_id = data.get('repo_id')
    if not repo_id:
        return JsonResponse({'error': 'repo_id is required.'}, status=400)
        
    repo = Repository.objects.filter(id=repo_id, user=request.user).first()
    if not repo:
        return JsonResponse({'error': 'Repository not found.'}, status=404)

    return JsonResponse({
        'repo_id': repo.id,
        'review': (
            f"### AI Code Review for {repo.full_name}\n\n"
            "Pull-request review is not enabled in this build yet. "
            "To avoid hallucinated reviews, Project DNA needs an actual PR diff before it can review changes. "
            "For now, use chat or Bug Hunt for read-only repository analysis."
        )
    })
        
    # Mocking a code review since we don't have a specific PR id in this simple flow
    try:
        review_msg = (
            f"### 🔍 AI Code Review for {repo.full_name}\n\n"
            f"**Pull Request #42: Refactor data pipelines & upgrade dependencies**\n\n"
            f"✅ **Architecture:** The separation of concerns in the new pipeline module is excellent.\n"
            f"⚠️ **Performance:** In `src/pipeline.js`, the nested `map()` over `filter()` might cause memory bloat on large datasets. Consider using a single `reduce()` pass.\n"
            f"📝 **Style:** Please ensure consistent use of type hints in the updated functions to adhere to the project's style guide.\n\n"
            f"**Conclusion:** Approve with minor suggestions. Code looks solid! 👍"
        )
        return JsonResponse({
            'repo_id': repo.id,
            'review': review_msg
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to generate code review: {str(e)}'}, status=500)

# Get Team Dashboard Stats
@csrf_exempt
def api_dashboard_stats(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
        
    try:
        # Calculate stats for the user's workspace
        total_repos = Repository.objects.filter(user=request.user).count()
        total_convos = Conversation.objects.filter(user=request.user).count()
        total_messages = Message.objects.filter(conversation__user=request.user).count()
        
        return JsonResponse({
            'total_repos': total_repos,
            'total_conversations': total_convos,
            'total_messages': total_messages,
            'bugs_found': total_repos * 3, # Mock stat
            'prs_reviewed': total_repos * 2, # Mock stat
            'code_written': total_messages * 15 # Mock stat
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to fetch dashboard stats: {str(e)}'}, status=500)


@csrf_exempt
def api_ai_apply_change(request):
    """Apply an explicit user-requested change and open a reviewable PR."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
    requested_change = data.get('request', '').strip()
    repo = Repository.objects.filter(id=data.get('repo_id'), user=request.user).first()
    if not repo or not requested_change:
        return JsonResponse({'error': 'repo_id and request are required.'}, status=400)
    github_token = getattr(getattr(request.user, 'profile', None), 'github_token', None)
    if not github_token:
        return JsonResponse({'error': 'Link GitHub with repository write access before creating a pull request.'}, status=403)

    chunks = search_relevant_chunks(repo, requested_change, top_k=3)
    if not chunks:
        return JsonResponse({'error': 'No indexed code matched this requested change.'}, status=409)
    target_path = chunks[0].file_path
    from repos.github_api import GitHubAPI, generate_branch_name
    github = GitHubAPI(github_token)
    owner, repo_name = repo.full_name.split('/', 1)
    file_data = github.get_file_content(owner, repo_name, target_path, repo.default_branch)
    if not file_data:
        return JsonResponse({'error': f'Could not read {target_path} from GitHub.'}, status=502)
    if len(file_data['content']) > 60000:
        return JsonResponse({'error': f'{target_path} is too large for a safe automatic replacement.'}, status=422)

    corrected_content = generate_fixed_file_content(target_path, file_data['content'], {
        'line': 'as needed', 'issue': requested_change, 'fix': requested_change,
    })
    if not corrected_content:
        return JsonResponse({'error': f'No safe complete-file change was generated for {target_path}.'}, status=422)
    branch_name = generate_branch_name('dna-change')
    branch_result = github.create_branch(owner, repo_name, branch_name, repo.default_branch)
    if not branch_result['success']:
        return JsonResponse({'error': f"Could not create a branch: {branch_result.get('error')}"}, status=502)
    commit_result = github.commit_file(
        owner, repo_name, target_path, corrected_content,
        f"Project DNA: {requested_change[:100]}", branch_name, file_data['sha'],
    )
    if not commit_result['success']:
        return JsonResponse({'error': 'Could not commit the generated change.', 'branch': branch_name}, status=502)
    pr_result = github.create_pull_request(
        owner, repo_name, f"Project DNA: {requested_change[:100]}",
        f"## Requested change\n\n{requested_change}\n\nPlease review this AI-generated change before merging.",
        branch_name, repo.default_branch,
    )
    if not pr_result['success']:
        return JsonResponse({'error': 'The change was committed but the pull request could not be opened.', 'branch': branch_name}, status=502)
    return JsonResponse({
        'success': True, 'file_path': target_path, 'branch': branch_name,
        'pr_created': True, 'pr_number': pr_result['pr_number'], 'pr_url': pr_result['pr_url'],
    })


@csrf_exempt
def api_ai_code_review_hf(request):
    """Review a real PR diff when available, otherwise indexed repository code."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    repo = Repository.objects.filter(id=data.get('repo_id'), user=request.user).first()
    if not repo:
        return JsonResponse({'error': 'Repository not found.'}, status=404)

    pr_number = data.get('pr_number')
    context, subject = '', 'repository code'
    github_token = getattr(getattr(request.user, 'profile', None), 'github_token', None)
    if github_token:
        from repos.github_api import GitHubAPI
        github = GitHubAPI(github_token)
        owner, repo_name = repo.full_name.split('/', 1)
        if not pr_number:
            open_prs = github.list_open_prs(owner, repo_name)
            pr_number = open_prs[0].get('number') if open_prs else None
        if pr_number:
            context = github.get_pull_request_diff(owner, repo_name, pr_number)[:30000]
            subject = f'pull request #{pr_number}'

    if not context:
        chunks = search_relevant_chunks(repo, 'code quality bugs security performance', top_k=8)
        context = '\n\n'.join(f'FILE: {chunk.file_path}\n{chunk.content}' for chunk in chunks)
    if not context:
        return JsonResponse({'error': 'No indexed code is available to review.'}, status=409)

    prompt = f'''You are a precise senior code reviewer. Review this {subject} from {repo.full_name}.
Only report issues directly supported by the supplied code or diff. Do not invent files or line numbers.

FORMAT YOUR RESPONSE USING MARKDOWN:
- Use headers (## ###) to organize sections: Summary, Findings, Suggested Fixes
- Use **bold** for emphasis and `code` for code references
- Use bullet points to list findings
- For each finding, include: severity level, file path, line number (if available), evidence from code, and concrete correction
- Never return a single dense paragraph
- Use code blocks (```language```) for code examples

{context}'''
    review = generate_ai_response(prompt, max_tokens=1400)
    return JsonResponse({'repo_id': repo.id, 'pr_number': pr_number, 'review': review})
