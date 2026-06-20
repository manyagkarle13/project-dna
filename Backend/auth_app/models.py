from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    github_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    github_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Repository(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositories')
    repo_url = models.URLField(max_length=500)
    full_name = models.CharField(max_length=255)
    default_branch = models.CharField(max_length=100, default='main')
    tech_stack = models.JSONField(default=list)
    ai_summary = models.TextField(blank=True, null=True)
    file_tree = models.JSONField(default=dict)
    file_count = models.IntegerField(default=0)
    total_size = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='ready')
    error_message = models.TextField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


