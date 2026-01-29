#!/usr/bin/env python3
"""
Test script for the QR Code Generator API endpoint.

This script tests the /api/v1/qr_code_generator endpoint with various inputs.
"""

import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/qr_code_generator"

# Test credentials - update these with actual credentials when testing
USERNAME = "admin"
PASSWORD = "admin"


def test_basic_qr_code():
    """Test basic QR code generation with default settings"""
    print("\n=== Test 1: Basic QR code with default settings ===")

    data = {
        "text": "https://github.com/andchir/various-useful-api-django"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_custom_size_and_colors():
    """Test QR code with custom size and colors"""
    print("\n=== Test 2: QR code with custom size and colors ===")

    data = {
        "text": "Hello, World!",
        "size": 15,
        "border": 2,
        "fill_color": "blue",
        "back_color": "yellow"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_high_error_correction():
    """Test QR code with high error correction"""
    print("\n=== Test 3: QR code with high error correction ===")

    data = {
        "text": "Test with high error correction",
        "error_correction": "H",
        "size": 12
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_missing_text():
    """Test with missing text (should fail)"""
    print("\n=== Test 4: Missing text field (should return error) ===")

    data = {
        "size": 10
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 422


def main():
    """Run all tests"""
    print("=" * 80)
    print("QR Code Generator API - Test Suite")
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
    results.append(("Basic QR code", test_basic_qr_code()))
    results.append(("Custom size and colors", test_custom_size_and_colors()))
    results.append(("High error correction", test_high_error_correction()))
    results.append(("Missing text field", test_missing_text()))

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
