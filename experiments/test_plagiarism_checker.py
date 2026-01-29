#!/usr/bin/env python3
"""
Test script for the Plagiarism Checker API endpoint.

This script tests the /api/v1/plagiarism_checker endpoint with various inputs.
"""

import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/plagiarism_checker"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin"


def test_identical_texts():
    """Test with identical texts (100% similarity)"""
    print("\n=== Test 1: Identical texts (should be 100% similar) ===")

    data = {
        "text1": "This is a sample text for plagiarism checking.",
        "text2": "This is a sample text for plagiarism checking.",
        "algorithm": "difflib"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200 and result.get('similarity_percentage', 0) >= 99


def test_similar_texts():
    """Test with similar texts"""
    print("\n=== Test 2: Similar texts (should have high similarity) ===")

    data = {
        "text1": "The quick brown fox jumps over the lazy dog.",
        "text2": "The quick brown fox jumps over a lazy dog.",
        "algorithm": "difflib"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_different_texts():
    """Test with completely different texts"""
    print("\n=== Test 3: Completely different texts (should have low similarity) ===")

    data = {
        "text1": "Python is a programming language.",
        "text2": "The weather today is sunny and warm.",
        "algorithm": "difflib"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200 and result.get('similarity_percentage', 100) < 50


def test_tfidf_algorithm():
    """Test with TF-IDF algorithm"""
    print("\n=== Test 4: Using TF-IDF algorithm ===")

    data = {
        "text1": "Machine learning is a subset of artificial intelligence that focuses on data.",
        "text2": "Artificial intelligence includes machine learning, which uses data to learn patterns.",
        "algorithm": "tfidf"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200


def test_missing_text():
    """Test with missing text (should fail)"""
    print("\n=== Test 5: Missing text2 field (should return error) ===")

    data = {
        "text1": "Only one text provided"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 422


def main():
    """Run all tests"""
    print("=" * 80)
    print("Plagiarism Checker API - Test Suite")
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
    results.append(("Identical texts", test_identical_texts()))
    results.append(("Similar texts", test_similar_texts()))
    results.append(("Different texts", test_different_texts()))
    results.append(("TF-IDF algorithm", test_tfidf_algorithm()))
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
