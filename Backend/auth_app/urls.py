from django.urls import path
from auth_app import views
from repos import pr_endpoints

urlpatterns = [
    # Frontend HTML serving
    path('', views.serve_index, name='serve_index'),
    path('dashboard.html', views.serve_dashboard, name='serve_dashboard'),

    # Local Auth APIs
    path('api/auth/signup', views.api_signup, name='api_signup'),
    path('api/auth/login', views.api_login, name='api_login'),
    path('api/auth/logout', views.api_logout, name='api_logout'),
    path('api/auth/me', views.api_me, name='api_me'),
    path('api/health', views.api_health, name='api_health'),

    # OAuth Routes
    path('auth/google', views.auth_google, name='auth_google'),
    path('auth/google/callback', views.auth_google_callback, name='auth_google_callback'),
    path('auth/github', views.auth_github, name='auth_github'),
    path('auth/github/callback', views.auth_github_callback, name='auth_github_callback'),
    path('api/auth/github/link', views.auth_github_link, name='auth_github_link'),
    path('api/auth/github/link/', views.auth_github_link, name='auth_github_link_slash'),

    # Mock Auth Sandbox
    path('auth/mock', views.auth_mock, name='auth_mock'),
    path('auth/mock/callback', views.auth_mock_callback, name='auth_mock_callback'),

    # Repositories APIs
    path('api/repos', views.api_repos_list, name='api_repos_list'),
    path('api/repos/', views.api_repos_list, name='api_repos_list_slash'),
    path('api/repos/github/list', views.api_github_repos_list, name='api_github_repos_list'),
    path('api/repos/github/list/', views.api_github_repos_list, name='api_github_repos_list_slash'),
    path('api/repos/connect', views.api_repos_connect, name='api_repos_connect'),
    path('api/repos/connect/', views.api_repos_connect, name='api_repos_connect_slash'),



    # AI ML Features
    path('api/ai/bug-hunt', views.api_ai_bug_hunt, name='api_ai_bug_hunt'),
    path('api/ai/bug-hunt/', views.api_ai_bug_hunt, name='api_ai_bug_hunt_slash'),
    path('api/ai/code-review', views.api_ai_code_review_hf, name='api_ai_code_review'),
    path('api/ai/code-review/', views.api_ai_code_review_hf, name='api_ai_code_review_slash'),
    path('api/ai/apply-change', views.api_ai_apply_change, name='api_ai_apply_change'),
    path('api/ai/apply-change/', views.api_ai_apply_change, name='api_ai_apply_change_slash'),

    # Repo Editor Features
    path('api/repos/file', views.api_repo_file, name='api_repo_file'),
    path('api/repos/file/', views.api_repo_file, name='api_repo_file_slash'),
    path('api/repos/create-pr-fix', views.api_create_pr_with_fix, name='api_create_pr_fix'),
    path('api/repos/create-pr-fix/', views.api_create_pr_with_fix, name='api_create_pr_fix_slash'),

    # Auto-fix via AI (generate fix and open PR)
    path('api/repos/<int:repo_id>/auto-fix', pr_endpoints.api_apply_fix_and_open_pr, name='api_auto_fix'),
    path('api/repos/<int:repo_id>/auto-fix/', pr_endpoints.api_apply_fix_and_open_pr, name='api_auto_fix_slash'),

    # Team Dashboard
    path('api/dashboard/stats', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats_slash'),
]
