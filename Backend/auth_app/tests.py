import json

from django.contrib.auth.models import User
from django.test import TestCase
from auth_app.models import UserProfile, Repository
from chat.models import Conversation, Message


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

    def test_write_endpoints_restricted_for_public_repo(self):
        user = User.objects.create_user(username='tester@example.com', password='secure-pass-123')
        UserProfile.objects.create(user=user, has_full_agent_access=True)
        self.client.force_login(user)

        repo = Repository.objects.create(
            user=user,
            repo_url="https://github.com/test-owner/test-repo",
            full_name="test-owner/test-repo",
            default_branch="main",
            source="public_url"  # not github_owned
        )

        # 1. Test api_ai_bug_hunt (auto_fix or create_pr should return 403)
        response = self.client.post(
            '/api/ai/bug-hunt/',
            data=json.dumps({'repo_id': repo.id, 'auto_fix': True, 'create_pr': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

        # 2. Test api_repo_file POST (should return 403)
        response = self.client.post(
            '/api/repos/file',
            data=json.dumps({'repo_id': repo.id, 'file_path': 'test.py', 'content': 'print(1)'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_write_endpoints_restricted_when_no_agent_access(self):
        user = User.objects.create_user(username='tester2@example.com', password='secure-pass-123')
        UserProfile.objects.create(user=user, has_full_agent_access=False) # Access is False
        self.client.force_login(user)

        repo = Repository.objects.create(
            user=user,
            repo_url="https://github.com/test-owner/test-repo",
            full_name="test-owner/test-repo",
            default_branch="main",
            source="github_owned"
        )

        # Test api_ai_bug_hunt (auto_fix or create_pr should return 403)
        response = self.client.post(
            '/api/ai/bug-hunt/',
            data=json.dumps({'repo_id': repo.id, 'auto_fix': True, 'create_pr': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_disconnect_repo_permanently_clears_repo_from_conversation(self):
        user = User.objects.create_user(username='tester3@example.com', password='secure-pass-123')
        self.client.force_login(user)

        repo = Repository.objects.create(
            user=user,
            repo_url="https://github.com/test-owner/test-repo",
            full_name="test-owner/test-repo",
            default_branch="main",
            source="github_owned"
        )

        conversation = Conversation.objects.create(user=user, repo=repo, title="Chat with Repo")

        # Verify repo is initially connected
        response = self.client.get(f'/api/chat/conversations/{conversation.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()['conversation']['connected_repo'])

        # Disconnect repo using PATCH
        patch_response = self.client.patch(
            f'/api/chat/conversations/{conversation.id}/',
            data=json.dumps({'disconnect_repo': True}),
            content_type='application/json'
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertTrue(patch_response.json()['success'])

        # Verify repo is now disconnected and persists as null
        get_response = self.client.get(f'/api/chat/conversations/{conversation.id}/')
        self.assertEqual(get_response.status_code, 200)
        self.assertIsNone(get_response.json()['conversation']['connected_repo'])

    def test_apply_fix_safety_checks(self):
        user = User.objects.create_user(username='tester_apply_fix@example.com', password='secure-pass-123')
        UserProfile.objects.create(user=user, has_full_agent_access=False)
        self.client.force_login(user)

        repo = Repository.objects.create(
            user=user,
            repo_url="https://github.com/test-owner/test-repo",
            full_name="test-owner/test-repo",
            default_branch="main",
            source="public_url"
        )

        response = self.client.post(
            f'/api/repos/{repo.id}/apply-fix/',
            data=json.dumps({'file_path': 'src/App.js', 'description': 'fix background'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_review_pr_safety_checks(self):
        user = User.objects.create_user(username='tester_review_pr@example.com', password='secure-pass-123')
        UserProfile.objects.create(user=user, has_full_agent_access=False)
        self.client.force_login(user)

        repo = Repository.objects.create(
            user=user,
            repo_url="https://github.com/test-owner/test-repo",
            full_name="test-owner/test-repo",
            default_branch="main",
            source="public_url"
        )

        response = self.client.post(
            f'/api/repos/{repo.id}/review-pr/',
            data=json.dumps({'pr_number': 42}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


