from django.db import models
from auth_app.models import Repository

class CodeChunk(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='chunks')
    file_path = models.CharField(max_length=1000)
    chunk_index = models.IntegerField()
    content = models.TextField()
    embedding = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['repo']),
        ]

    def __str__(self):
        return f"{self.repo.full_name} - {self.file_path} - Chunk {self.chunk_index}"
