"""
Git link analysis endpoint - analyze and fix any repo
"""
import json
import threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from chat.models import Conversation, Message
from auth_app.models import Repository
from chat.repo_analyzer import RepoAnalyzer


@csrf_exempt
def api_analyze_git_link(request):
    """
    Analyze a git link: detect bugs, tech stack, and suggest fixes
    NO PR created - just analysis and fixes
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    git_link = data.get('git_link', '').strip()
    if not git_link:
        return JsonResponse({'error': 'Git link is required.'}, status=400)

    # Validate it's a git URL
    if not ('github.com' in git_link or 'gitlab.com' in git_link or '.git' in git_link):
        return JsonResponse({'error': 'Invalid git URL.'}, status=400)

    try:
        # Run analyzer in background to not block response
        analyzer = RepoAnalyzer(git_link)
        analysis_result = analyzer.analyze()

        if 'error' in analysis_result:
            return JsonResponse(analysis_result, status=400)

        # Create or get conversation for this repo
        repo_name = git_link.split('/')[-1].replace('.git', '')
        conversation = Conversation.objects.create(
            user=request.user,
            title=f"Analysis: {repo_name}",
            repo=None  # No DB repo, external analysis
        )

        # Save analysis as assistant message
        analysis_message = f"""
{analysis_result['summary']}

### Deployment Fixes Ready:
{format_fixes(analysis_result.get('fixes_suggested', []))}

**No PR will be created.** This analysis is for your reference.
You can ask questions about the code or apply these fixes manually.
"""

        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=analysis_message
        )

        # Store analysis data in conversation for reference
        Message.objects.create(
            conversation=conversation,
            role='system',
            content=json.dumps(analysis_result)  # System metadata
        )

        return JsonResponse({
            'conversation_id': conversation.id,
            'analysis': analysis_result,
            'message': analysis_message,
            'status': 'Analysis complete - no PR created'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def format_fixes(fixes: list) -> str:
    """Format suggested fixes for display"""
    if not fixes:
        return "✅ No critical issues found"

    fix_descriptions = {
        'dynamic_port': '🔧 Use $PORT environment variable for dynamic port binding (Render)',
        'shell_form_cmd': '🔧 Convert Dockerfile CMD to shell form for env variable expansion',
        'add_migrations': '🔧 Add entrypoint.sh to run migrations on container startup',
        'add_gunicorn': '🔧 Add gunicorn to requirements.txt for production'
    }

    formatted = ""
    for fix in fixes:
        formatted += f"- {fix_descriptions.get(fix, fix)}\n"

    return formatted


@csrf_exempt
def api_analyze_repo_for_chat(request):
    """
    Simple endpoint to get repo analysis without conversation
    Useful for dashboard summaries
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    git_link = data.get('git_link', '').strip()
    if not git_link:
        return JsonResponse({'error': 'Git link is required.'}, status=400)

    try:
        analyzer = RepoAnalyzer(git_link)
        analysis_result = analyzer.analyze()

        if 'error' in analysis_result:
            return JsonResponse(analysis_result, status=400)

        return JsonResponse({
            'analysis': analysis_result,
            'status': 'success'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
