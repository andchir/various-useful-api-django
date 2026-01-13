import asyncio
import json
import os
import uuid
import logging
from django.http import HttpResponse
from rest_framework.authentication import BasicAuthentication
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from app import settings
from main.lib import delete_old_files
from main.serializers import WebsiteScreenshotRequestSerializer, WebsiteScreenshotResponseSerializer, \
    WebsiteScreenshotErrorSerializer

logger = logging.getLogger('django')


@extend_schema(
    tags=['Screenshot'],
    request=WebsiteScreenshotRequestSerializer,
    responses={
        (200, 'application/json'): WebsiteScreenshotResponseSerializer,
        (422, 'application/json'): WebsiteScreenshotErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def website_screenshot(request):
    """
    API endpoint for creating website screenshots.
    Accepts URL, width, height, and full page parameters.
    Uses 20 second timeout for unresponsive websites.
    """
    url = request.data.get('url')
    width = request.data.get('width')
    height = request.data.get('height')
    full = request.data.get('full', False)

    # Validate required fields
    if not url:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'URL is required.'}),
            content_type='application/json',
            status=422
        )

    if not width or not height:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Width and height are required.'}),
            content_type='application/json',
            status=422
        )

    try:
        width = int(width)
        height = int(height)
    except (ValueError, TypeError):
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Width and height must be integers.'}),
            content_type='application/json',
            status=422
        )

    # Validate dimensions
    if width < 1 or width > 3840:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Width must be between 1 and 3840 pixels.'}),
            content_type='application/json',
            status=422
        )

    if height < 1 or height > 2160:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Height must be between 1 and 2160 pixels.'}),
            content_type='application/json',
            status=422
        )

    # Validate full parameter
    if isinstance(full, str):
        full = full.lower() in ['true', '1', 'yes']
    else:
        full = bool(full)

    # Create screenshots directory if it doesn't exist
    screenshots_dir = os.path.join(settings.MEDIA_ROOT, 'screenshots')
    if not os.path.isdir(screenshots_dir):
        os.makedirs(screenshots_dir)

    # Delete old files
    delete_old_files(screenshots_dir, max_hours=1)

    # Generate unique filename for the screenshot
    screenshot_uuid = uuid.uuid1()
    screenshot_path = os.path.join(screenshots_dir, f'{screenshot_uuid}.png')

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)

            # Set viewport size
            context = browser.new_context(
                viewport={'width': width, 'height': height}
            )

            # Create a new page
            page = context.new_page()

            # Set timeout to 20 seconds as required
            page.set_default_timeout(20000)

            try:
                # Navigate to URL with timeout
                page.goto(url, wait_until='networkidle', timeout=20000)

                # Take screenshot
                page.screenshot(
                    path=screenshot_path,
                    full_page=full
                )

            except PlaywrightTimeoutError:
                browser.close()
                return HttpResponse(
                    json.dumps({'success': False, 'message': 'Website did not respond within 20 seconds.'}),
                    content_type='application/json',
                    status=422
                )
            except Exception as e:
                browser.close()
                logger.error(f'Error taking screenshot: {str(e)}')
                return HttpResponse(
                    json.dumps({'success': False, 'message': f'Error loading website: {str(e)}'}),
                    content_type='application/json',
                    status=422
                )

            # Close browser
            browser.close()

        # Return the URL to the screenshot
        host_url = f"{request.scheme}://{request.get_host()}"
        screenshot_url = f"{host_url}/media/screenshots/{screenshot_uuid}.png"

        output = {
            'success': True,
            'screenshot_url': screenshot_url
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f'Error creating screenshot: {str(e)}')
        if os.path.exists(screenshot_path):
            os.unlink(screenshot_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Error: {str(e)}'}),
            content_type='application/json',
            status=422
        )
