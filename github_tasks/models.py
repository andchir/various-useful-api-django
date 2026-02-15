"""
GitHub Task models for tracking issue solving tasks.
"""
import uuid
from django.db import models


class GitHubTask(models.Model):
    """
    Model for GitHub issue solving tasks.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('canceled', 'Canceled'),
    )

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='Date created')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Date updated')
    issue_link = models.URLField(max_length=500, verbose_name='GitHub issue link')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    owner = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Repository owner'
    )
    is_private = models.BooleanField(default=False, verbose_name='Is private repository')
    tool = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Tool name'
    )
    model = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='AI model name'
    )
    email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name='Email for notifications'
    )
    telegram_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Telegram user ID for notifications'
    )

    class Meta:
        db_table = 'github_tasks'
        verbose_name = 'GitHub Task'
        verbose_name_plural = 'GitHub Tasks'
        ordering = ['-date_created']

    def __str__(self):
        return f"Task {self.uuid} - {self.issue_link} ({self.get_status_display()})"
