import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from chat.models import Conversation, Message
from auth_app.models import Repository
from chat.agent import generate_agent_response

@csrf_exempt
def api_chat_send(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
        
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        
    message_text = data.get('message', '').strip()
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
        
    conversation_id = data.get('conversation_id')
    repo_id = data.get('repo_id')
    
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found.'}, status=404)
    else:
        repo = None
        title = "New Chat"
        if repo_id:
            try:
                repo = Repository.objects.get(id=repo_id, user=request.user)
                title = f"Chat: {repo.full_name.split('/')[-1]}"
            except Repository.DoesNotExist:
                return JsonResponse({'error': 'Repository not found.'}, status=404)
                
        conversation = Conversation.objects.create(user=request.user, repo=repo, title=title)
        
    # Save user message
    Message.objects.create(conversation=conversation, role='user', content=message_text)
    
    # Generate agent response
    agent_text = generate_agent_response(conversation, message_text)
    
    # Save agent message
    assistant_msg = Message.objects.create(conversation=conversation, role='assistant', content=agent_text)
    
    # Update title if it was New Chat and we have a repo
    if conversation.title == "New Chat" and conversation.repo:
        conversation.title = f"Chat: {conversation.repo.full_name.split('/')[-1]}"
        conversation.save()

    return JsonResponse({
        'conversation_id': conversation.id,
        'conversation_title': conversation.title,
        'ai_message': {
            'id': assistant_msg.id,
            'sender': assistant_msg.role,
            'text': assistant_msg.content,
            'created_at': assistant_msg.created_at.isoformat()
        }
    })

@csrf_exempt
def api_chat_conversations(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    if request.method == 'GET':
        conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
        data = []
        for c in conversations:
            data.append({
                'id': c.id,
                'title': c.title,
                'repo_id': c.repo.id if c.repo else None,
                'updated_at': c.updated_at.isoformat()
            })
        return JsonResponse({'conversations': data})
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
            
        title = data.get('title', 'New Chat')
        repo_id = data.get('repo_id')
        repo = None
        if repo_id:
            try:
                repo = Repository.objects.get(id=repo_id, user=request.user)
                if title == 'New Chat' or title == '':
                    title = f"Chat: {repo.full_name.split('/')[-1]}"
            except Repository.DoesNotExist:
                return JsonResponse({'error': 'Repository not found.'}, status=404)
                
        conversation = Conversation.objects.create(user=request.user, repo=repo, title=title)
        
        # Automatically post the summary message if a repository is linked
        if repo:
            ai_text = (
                f"I've successfully connected to **{repo.full_name}**.\n\n"
                f"**Detected Stack:** {', '.join(repo.tech_stack)}\n\n"
                f"{repo.ai_summary}"
            )
            Message.objects.create(conversation=conversation, role='assistant', content=ai_text)

        return JsonResponse({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'updated_at': conversation.updated_at.isoformat()
            }
        }, status=201)
        
    return JsonResponse({'error': 'Method not allowed.'}, status=405)

@csrf_exempt
def api_chat_conversation_detail(request, conversation_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)
        
    if request.method == 'GET':
        messages = conversation.messages.order_by('created_at')
        msgs_data = []
        for m in messages:
            msgs_data.append({
                'id': m.id,
                'sender': m.role,
                'text': m.content,
                'created_at': m.created_at.isoformat()
            })
            
        return JsonResponse({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'connected_repo': {
                    'id': conversation.repo.id,
                    'repo_url': conversation.repo.repo_url,
                    'full_name': conversation.repo.full_name,
                    'default_branch': conversation.repo.default_branch,
                    'tech_stack': conversation.repo.tech_stack,
                    'ai_summary': conversation.repo.ai_summary,
                    'file_tree': conversation.repo.file_tree,
                    'file_count': conversation.repo.file_count,
                    'total_size': conversation.repo.total_size,
                    'source': conversation.repo.source,
                    'connected_at': conversation.repo.connected_at.isoformat()
                } if conversation.repo else None
            },
            'messages': msgs_data
        })
        
    elif request.method == 'PATCH':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
            
        if data.get('disconnect_repo') is True or ('repo_id' in data and data['repo_id'] is None):
            conversation.repo = None
            conversation.save()
            return JsonResponse({'success': True, 'message': 'Repository disconnected from conversation.'})
        
        return JsonResponse({'error': 'Invalid request parameters.'}, status=400)
        
    elif request.method == 'DELETE':
        conversation.delete()
        return JsonResponse({'message': 'Conversation deleted successfully.'})

    return JsonResponse({'error': 'Method not allowed.'}, status=405)

@csrf_exempt
def api_save_message(request, conversation_id):
    """Save a message to a conversation (for frontend-generated messages like PR results)."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    message_text = data.get('message', '').strip()
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    # Save message to database
    msg = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=message_text
    )

    return JsonResponse({
        'message': {
            'id': msg.id,
            'sender': msg.role,
            'text': msg.content,
            'created_at': msg.created_at.isoformat()
        }
    }, status=201)
