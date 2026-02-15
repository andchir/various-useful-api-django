"""
Views for GitHub task management API.
"""
import os
import logging
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import requests

from github_tasks.models import GitHubTask
from github_tasks.serializers import (
    GitHubTaskCreateSerializer,
    GitHubTaskResponseSerializer,
    GitHubTaskStatusUpdateSerializer,
    GitHubTaskListSerializer,
    ErrorResponseSerializer
)

logger = logging.getLogger(__name__)


class GitHubTaskPagination(PageNumberPagination):
    """Custom pagination for GitHub task list."""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


def send_email_notification(task):
    """Send email notification about task status change."""
    if not task.email:
        return

    try:
        subject = f"GitHub Task {task.uuid} - Status: {task.get_status_display()}"
        message = f"""
Your GitHub task status has been updated.

Task UUID: {task.uuid}
Issue Link: {task.issue_link}
Status: {task.get_status_display()}
Updated at: {task.date_updated}

This is an automated notification.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[task.email],
            fail_silently=False,
        )
        logger.info(f"Email notification sent to {task.email} for task {task.uuid}")
    except Exception as e:
        logger.error(f"Failed to send email notification for task {task.uuid}: {str(e)}")


def send_telegram_notification(task):
    """Send Telegram notification about task status change."""
    if not task.telegram_id:
        return

    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured, skipping Telegram notification")
        return

    try:
        message = f"""
🤖 GitHub Task Update

📋 Task UUID: {task.uuid}
🔗 Issue: {task.issue_link}
📊 Status: {task.get_status_display()}
🕐 Updated: {task.date_updated.strftime('%Y-%m-%d %H:%M:%S')}
        """

        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': task.telegram_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram notification sent to {task.telegram_id} for task {task.uuid}")
        else:
            logger.error(f"Failed to send Telegram notification: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification for task {task.uuid}: {str(e)}")


@extend_schema(
    tags=['GitHub Tasks'],
    request=GitHubTaskCreateSerializer,
    responses={
        201: GitHubTaskResponseSerializer,
        400: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def task_create(request):
    """
    Create a new GitHub task.
    Returns task data including UUID.
    """
    try:
        serializer = GitHubTaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = GitHubTaskResponseSerializer(task, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Task creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['GitHub Tasks'],
    responses={
        200: GitHubTaskResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def task_detail(request, task_uuid):
    """
    Get a single GitHub task by UUID.
    """
    try:
        try:
            task = GitHubTask.objects.get(uuid=task_uuid)
        except GitHubTask.DoesNotExist:
            return Response({'success': False, 'message': 'Task not found'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = GitHubTaskResponseSerializer(task, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Task detail error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['GitHub Tasks'],
    parameters=[
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by status (pending, processing, completed, error, canceled)',
            required=False
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of items per page (default: 10, max: 100)',
            required=False
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Page number',
            required=False
        ),
    ],
    responses={
        200: GitHubTaskListSerializer(many=True),
        400: ErrorResponseSerializer,
    },
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def task_list(request):
    """
    Get list of GitHub tasks with optional status filter and pagination.

    Query parameters:
    - status: Filter by task status (optional)
    - limit: Number of items per page (default: 10, max: 100)
    - page: Page number
    """
    try:
        queryset = GitHubTask.objects.all()

        # Filter by status if provided
        status_filter = request.query_params.get('status', None)
        if status_filter:
            if status_filter not in ['pending', 'processing', 'completed', 'error', 'canceled']:
                return Response(
                    {'success': False, 'message': 'Invalid status value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(status=status_filter)

        # Apply pagination
        paginator = GitHubTaskPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = GitHubTaskListSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        logger.error(f"Task list error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['GitHub Tasks'],
    request=GitHubTaskStatusUpdateSerializer,
    responses={
        200: GitHubTaskResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def task_status_update(request, task_uuid):
    """
    Update task status by UUID.
    Sends email and/or Telegram notifications if configured.
    """
    try:
        try:
            task = GitHubTask.objects.get(uuid=task_uuid)
        except GitHubTask.DoesNotExist:
            return Response({'success': False, 'message': 'Task not found'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = GitHubTaskStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            old_status = task.status
            new_status = serializer.validated_data['status']

            task.status = new_status
            task.save()

            # Send notifications on status change
            if old_status != new_status:
                send_email_notification(task)
                send_telegram_notification(task)

            response_serializer = GitHubTaskResponseSerializer(task, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Task status update error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
