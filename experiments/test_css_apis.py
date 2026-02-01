#!/usr/bin/env python3
"""
Test script for CSS Tools API endpoints.

This script tests all 6 CSS-related API endpoints:
1. SVG to CSS background-image URL converter
2. CSS Gradient Generator
3. CSS Box Shadow Generator
4. CSS Transform Generator
5. CSS Animation/Keyframes Generator
6. CSS Filter Effects Generator
"""

import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"

# Test credentials - update these with actual credentials when testing
USERNAME = "admin"
PASSWORD = "admin"


def test_svg_to_css_background():
    """Test SVG to CSS background-image URL converter"""
    print("\n=== Test 1: SVG to CSS background-image URL ===")

    API_URL = f"{BASE_URL}/api/v1/svg_to_css_background"

    data = {
        "svg_code": '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="red"/></svg>'
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_css_gradient_generator():
    """Test CSS Gradient Generator"""
    print("\n=== Test 2: CSS Gradient Generator ===")

    API_URL = f"{BASE_URL}/api/v1/css_gradient_generator"

    # Test linear gradient
    data = {
        "type": "linear",
        "colors": [
            {"color": "#ff0000", "position": 0},
            {"color": "#0000ff", "position": 100}
        ],
        "angle": 90
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_css_gradient_generator_radial():
    """Test CSS Gradient Generator with radial gradient"""
    print("\n=== Test 2b: CSS Gradient Generator (Radial) ===")

    API_URL = f"{BASE_URL}/api/v1/css_gradient_generator"

    data = {
        "type": "radial",
        "colors": [
            {"color": "yellow"},
            {"color": "orange"},
            {"color": "red"}
        ],
        "shape": "circle",
        "position": "center"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_css_box_shadow_generator():
    """Test CSS Box Shadow Generator"""
    print("\n=== Test 3: CSS Box Shadow Generator ===")

    API_URL = f"{BASE_URL}/api/v1/css_box_shadow_generator"

    data = {
        "h_offset": 5,
        "v_offset": 5,
        "blur": 15,
        "spread": 2,
        "color": "rgba(0, 0, 0, 0.3)",
        "inset": False
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_css_transform_generator():
    """Test CSS Transform Generator"""
    print("\n=== Test 4: CSS Transform Generator ===")

    API_URL = f"{BASE_URL}/api/v1/css_transform_generator"

    data = {
        "operations": [
            {"type": "rotate", "value": "45deg"},
            {"type": "scale", "value": "1.5"},
            {"type": "translateX", "value": "20px"}
        ]
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_css_animation_generator():
    """Test CSS Animation/Keyframes Generator"""
    print("\n=== Test 5: CSS Animation/Keyframes Generator ===")

    API_URL = f"{BASE_URL}/api/v1/css_animation_generator"

    data = {
        "name": "fadeIn",
        "keyframes": [
            {"percentage": 0, "properties": {"opacity": "0", "transform": "translateY(-20px)"}},
            {"percentage": 100, "properties": {"opacity": "1", "transform": "translateY(0)"}}
        ],
        "duration": "0.5s",
        "timing_function": "ease-in-out",
        "iteration_count": "1",
        "direction": "normal",
        "fill_mode": "forwards"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def test_css_filter_generator():
    """Test CSS Filter Effects Generator"""
    print("\n=== Test 6: CSS Filter Effects Generator ===")

    API_URL = f"{BASE_URL}/api/v1/css_filter_generator"

    data = {
        "filters": [
            {"type": "blur", "value": "5px"},
            {"type": "brightness", "value": "1.2"},
            {"type": "contrast", "value": "1.5"}
        ]
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def main():
    """Run all tests"""
    print("=" * 80)
    print("CSS Tools API - Comprehensive Test Suite")
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
    results.append(("SVG to CSS background", test_svg_to_css_background()))
    results.append(("CSS Gradient Generator (Linear)", test_css_gradient_generator()))
    results.append(("CSS Gradient Generator (Radial)", test_css_gradient_generator_radial()))
    results.append(("CSS Box Shadow Generator", test_css_box_shadow_generator()))
    results.append(("CSS Transform Generator", test_css_transform_generator()))
    results.append(("CSS Animation Generator", test_css_animation_generator()))
    results.append(("CSS Filter Generator", test_css_filter_generator()))

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
