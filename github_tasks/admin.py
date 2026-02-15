"""
Admin interface configuration for GitHub tasks.
"""
from django.contrib import admin
from github_tasks.models import GitHubTask


@admin.register(GitHubTask)
class GitHubTaskAdmin(admin.ModelAdmin):
    """Admin configuration for GitHub Task model."""
    list_display = ('uuid', 'issue_link', 'status', 'owner', 'is_private', 'date_created', 'date_updated')
    list_filter = ('status', 'is_private', 'date_created', 'date_updated')
    search_fields = ('uuid', 'issue_link', 'owner', 'email', 'telegram_id')
    readonly_fields = ('uuid', 'date_created', 'date_updated')
    ordering = ('-date_created',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('uuid', 'issue_link', 'status', 'owner', 'is_private')
        }),
        ('Configuration', {
            'fields': ('tool', 'model')
        }),
        ('Notifications', {
            'fields': ('email', 'telegram_id')
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        }),
    )
