from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source_file = models.FileField(upload_to='project_files/', blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class APIEndpoint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='endpoints')
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=50) # e.g. GET, POST
    name = models.CharField(max_length=255) # function/class name
    description = models.TextField(blank=True) # generated or extracted
    category = models.CharField(max_length=100, blank=True)
    path_params = models.JSONField(blank=True, null=True)
    source_file = models.CharField(max_length=500, blank=True)  # which .py file it came from
    request_schema = models.JSONField(blank=True, null=True)
    response_schema = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.method} {self.path}"
