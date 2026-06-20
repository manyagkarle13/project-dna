import json

from django.contrib.auth.models import User
from django.test import TestCase


class AuthenticationAndRepositorySmokeTests(TestCase):
    def test_signup_and_current_user(self):
        response = self.client.post(
            '/api/auth/signup',
            data=json.dumps({'name': 'Test User', 'email': 'test@example.com', 'password': 'secure-pass-123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['email'], 'test@example.com')

    def test_dashboard_requires_authentication(self):
        response = self.client.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 401)

    def test_conversation_can_be_created_for_a_connected_repo(self):
        user = User.objects.create_user(username='owner@example.com', password='secure-pass-123')
        self.client.force_login(user)
        response = self.client.post(
            '/api/chat/conversations/',
            data=json.dumps({'title': 'New Chat'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('conversation', response.json())
