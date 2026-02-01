#!/usr/bin/env python3
"""
Test script for the widget embed code generator API endpoint.

This script tests the /api/v1/widget_embed_code endpoint with various inputs.
"""

import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/widget_embed_code"

# Test credentials - update these with actual credentials when testing
USERNAME = "admin"
PASSWORD = "admin"


def test_basic_request():
    """Test basic request with only required fields"""
    print("\n=== Test 1: Basic request with only required field ===")

    data = {
        "app_embed_url": "https://api2app.org/ru/apps/embed/cd635a6f-41a8-4d24-800e-4f950f3e128f"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n=== Generated Embed Code ===")
            print(result['embed_code'])

    return response.status_code == 200


def test_full_request():
    """Test full request with all fields including social media buttons"""
    print("\n=== Test 2: Full request with all fields ===")

    data = {
        "app_embed_url": "https://api2app.org/ru/apps/embed/cd635a6f-41a8-4d24-800e-4f950f3e128f",
        "button_color": "#007bff",
        "hover_color": "#0056b3",
        "position": "bottom-right",
        "width": 350,
        "height": 455,
        "button_text": "Открыть чат",
        "whatsapp_text": "Позвоните нам!",
        "whatsapp_href": "https://wa.me/1234567890",
        "telegram_text": "Мы в Телеграм!",
        "telegram_href": "https://t.me/example",
        "vk_text": "Мы в VK!",
        "vk_href": "https://vk.com/example",
        "instagram_text": "Мы в Instagram!",
        "instagram_href": "https://instagram.com/example",
        "facebook_text": "Мы в Facebook!",
        "facebook_href": "https://facebook.com/example",
        "youtube_text": "Наш YouTube-канал",
        "youtube_href": "https://youtube.com/@example",
        "tiktok_text": "Мы в TikTok!",
        "tiktok_href": "https://tiktok.com/@example"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n=== Generated Embed Code ===")
            print(result['embed_code'])

    return response.status_code == 200


def test_partial_social_media():
    """Test with only some social media buttons"""
    print("\n=== Test 3: Partial social media buttons (only WhatsApp and Telegram) ===")

    data = {
        "app_embed_url": "https://api2app.org/ru/apps/embed/cd635a6f-41a8-4d24-800e-4f950f3e128f",
        "button_text": "Чат с нами",
        "whatsapp_text": "WhatsApp",
        "whatsapp_href": "https://wa.me/1234567890",
        "telegram_text": "Telegram",
        "telegram_href": "https://t.me/example"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n=== Generated Embed Code ===")
            print(result['embed_code'])

    return response.status_code == 200


def test_youtube_tiktok():
    """Test with YouTube and TikTok buttons"""
    print("\n=== Test 4: YouTube and TikTok buttons ===")

    data = {
        "app_embed_url": "https://api2app.org/ru/apps/embed/cd635a6f-41a8-4d24-800e-4f950f3e128f",
        "button_text": "Открыть чат",
        "youtube_text": "Наш YouTube-канал",
        "youtube_href": "https://youtube.com/@example",
        "tiktok_text": "Мы в TikTok!",
        "tiktok_href": "https://tiktok.com/@example"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n=== Generated Embed Code ===")
            print(result['embed_code'])

    return response.status_code == 200


def test_different_position():
    """Test with different widget position"""
    print("\n=== Test 5: Different position (top-left) ===")

    data = {
        "app_embed_url": "https://api2app.org/ru/apps/embed/cd635a6f-41a8-4d24-800e-4f950f3e128f",
        "position": "top-left",
        "width": 400,
        "height": 500
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("\n=== Generated Embed Code ===")
            print(result['embed_code'])

    return response.status_code == 200


def test_missing_required_field():
    """Test with missing required field (should fail)"""
    print("\n=== Test 6: Missing required field (should return error) ===")

    data = {
        "button_color": "#007bff"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    return response.status_code == 422


def main():
    """Run all tests"""
    print("=" * 80)
    print("Widget Embed Code Generator API - Test Suite")
    print("=" * 80)

    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"\nServer is running at {BASE_URL}")
    except requests.exceptions.RequestException as e:
        print(f"\nError: Cannot connect to server at {BASE_URL}")
        print(f"Please ensure the Django development server is running.")
        print(f"Start it with: python manage.py runserver")
        return

    # Run tests
    results = []
    results.append(("Basic request", test_basic_request()))
    results.append(("Full request with all fields", test_full_request()))
    results.append(("Partial social media buttons", test_partial_social_media()))
    results.append(("YouTube and TikTok buttons", test_youtube_tiktok()))
    results.append(("Different position", test_different_position()))
    results.append(("Missing required field", test_missing_required_field()))

    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    print("=" * 80)


if __name__ == "__main__":
    main()
