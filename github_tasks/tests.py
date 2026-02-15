"""
Unit tests for GitHub task management.
"""
import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from github_tasks.models import GitHubTask


class GitHubTaskModelTests(TestCase):
    """Tests for GitHubTask model."""

    def test_create_task(self):
        """Test creating a GitHub task."""
        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            owner='owner',
            is_private=False,
            status='pending'
        )
        self.assertIsNotNone(task.uuid)
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.owner, 'owner')
        self.assertFalse(task.is_private)

    def test_task_string_representation(self):
        """Test task string representation."""
        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            status='processing'
        )
        expected = f"Task {task.uuid} - https://github.com/owner/repo/issues/1 (Processing)"
        self.assertEqual(str(task), expected)

    def test_task_status_choices(self):
        """Test all valid status choices."""
        statuses = ['pending', 'processing', 'completed', 'error', 'canceled']
        for status_value in statuses:
            task = GitHubTask.objects.create(
                issue_link='https://github.com/owner/repo/issues/1',
                status=status_value
            )
            self.assertEqual(task.status, status_value)


class GitHubTaskAPITests(TestCase):
    """Tests for GitHub task API endpoints."""

    def setUp(self):
        """Set up test client and sample data."""
        self.client = Client()

    def test_create_task_success(self):
        """Test successful task creation via API."""
        url = reverse('github_task_create')
        data = {
            'issue_link': 'https://github.com/owner/repo/issues/1',
            'owner': 'owner',
            'is_private': False,
            'email': 'test@example.com'
        }
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('uuid', response.json())
        self.assertEqual(response.json()['issue_link'], data['issue_link'])
        self.assertEqual(response.json()['status'], 'pending')

    def test_create_task_invalid_url(self):
        """Test task creation with invalid GitHub URL."""
        url = reverse('github_task_create')
        data = {
            'issue_link': 'https://example.com/issues/1',
        }
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_task_detail(self):
        """Test retrieving a single task by UUID."""
        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            owner='owner'
        )
        url = reverse('github_task_detail', kwargs={'task_uuid': task.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['uuid'], str(task.uuid))

    def test_get_task_detail_not_found(self):
        """Test retrieving non-existent task."""
        fake_uuid = uuid.uuid4()
        url = reverse('github_task_detail', kwargs={'task_uuid': fake_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_tasks(self):
        """Test listing tasks without filter."""
        GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            status='pending'
        )
        GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/2',
            status='completed'
        )
        url = reverse('github_task_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 2)

    def test_list_tasks_with_status_filter(self):
        """Test listing tasks with status filter."""
        GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            status='pending'
        )
        GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/2',
            status='completed'
        )
        url = reverse('github_task_list')
        response = self.client.get(url, {'status': 'pending'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['status'], 'pending')

    def test_list_tasks_with_pagination(self):
        """Test task list pagination."""
        for i in range(15):
            GitHubTask.objects.create(
                issue_link=f'https://github.com/owner/repo/issues/{i}',
                status='pending'
            )
        url = reverse('github_task_list')
        response = self.client.get(url, {'limit': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)

    @patch('github_tasks.views.send_email_notification')
    @patch('github_tasks.views.send_telegram_notification')
    def test_update_task_status(self, mock_telegram, mock_email):
        """Test updating task status."""
        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            status='pending'
        )
        url = reverse('github_task_status_update', kwargs={'task_uuid': task.uuid})
        data = {'status': 'processing'}
        response = self.client.patch(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'processing')

        # Verify notifications were called
        mock_email.assert_called_once()
        mock_telegram.assert_called_once()

    def test_update_task_status_invalid(self):
        """Test updating task with invalid status."""
        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            status='pending'
        )
        url = reverse('github_task_status_update', kwargs={'task_uuid': task.uuid})
        data = {'status': 'invalid_status'}
        response = self.client.patch(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificationTests(TestCase):
    """Tests for notification functions."""

    @patch('github_tasks.views.send_mail')
    def test_email_notification(self, mock_send_mail):
        """Test email notification sending."""
        from github_tasks.views import send_email_notification

        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            email='test@example.com',
            status='completed'
        )
        send_email_notification(task)
        mock_send_mail.assert_called_once()

    @patch('github_tasks.views.requests.post')
    @patch('os.environ.get')
    def test_telegram_notification(self, mock_env_get, mock_post):
        """Test Telegram notification sending."""
        from github_tasks.views import send_telegram_notification

        mock_env_get.return_value = 'fake_token'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        task = GitHubTask.objects.create(
            issue_link='https://github.com/owner/repo/issues/1',
            telegram_id='123456',
            status='completed'
        )
        send_telegram_notification(task)
        mock_post.assert_called_once()
