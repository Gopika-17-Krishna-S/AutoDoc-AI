from django.contrib import admin
from .models import Project, APIEndpoint

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'endpoint_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'user__username')
    ordering = ('-created_at',)

    def endpoint_count(self, obj):
        return obj.endpoints.count()
    endpoint_count.short_description = 'Endpoints'

@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    list_display = ('method', 'path', 'name', 'category', 'project')
    list_filter = ('method', 'category')
    search_fields = ('path', 'name', 'description')
    ordering = ('project', 'category', 'path')
