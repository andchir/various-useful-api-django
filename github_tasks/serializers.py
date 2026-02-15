"""
Serializers for GitHub task management.
"""
from rest_framework import serializers
from github_tasks.models import GitHubTask


class GitHubTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new GitHub task."""

    class Meta:
        model = GitHubTask
        fields = ('issue_link', 'owner', 'is_private', 'tool', 'model', 'email', 'telegram_id')
        extra_kwargs = {
            'is_private': {'default': False},
        }

    def validate_issue_link(self, value):
        """Validate that the issue_link is a valid GitHub URL."""
        if not value.startswith('https://github.com/'):
            raise serializers.ValidationError("Issue link must be a valid GitHub URL starting with 'https://github.com/'")
        return value


class GitHubTaskResponseSerializer(serializers.ModelSerializer):
    """Serializer for GitHub task responses."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GitHubTask
        fields = (
            'uuid', 'date_created', 'date_updated', 'issue_link', 'status',
            'status_display', 'owner', 'is_private', 'tool', 'model', 'email',
            'telegram_id'
        )
        read_only_fields = ('uuid', 'date_created', 'date_updated', 'status', 'status_display')


class GitHubTaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status."""
    status = serializers.ChoiceField(
        choices=['pending', 'processing', 'completed', 'error', 'canceled'],
        required=True
    )


class GitHubTaskListSerializer(serializers.ModelSerializer):
    """Serializer for listing GitHub tasks."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GitHubTask
        fields = (
            'uuid', 'date_created', 'date_updated', 'issue_link', 'status',
            'status_display', 'owner', 'is_private'
        )
        read_only_fields = fields


class ErrorResponseSerializer(serializers.Serializer):
    """Generic error response serializer."""
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
