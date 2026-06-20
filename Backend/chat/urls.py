from django.urls import path
from chat.views import api_chat_send, api_chat_conversations, api_chat_conversation_detail

urlpatterns = [
    path('send/', api_chat_send, name='api_chat_send'),
    path('conversations/', api_chat_conversations, name='api_chat_conversations'),
    path('conversations/<int:conversation_id>/', api_chat_conversation_detail, name='api_chat_conversation_detail'),
]
