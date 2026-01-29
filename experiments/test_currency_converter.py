#!/usr/bin/env python3
"""
Test script for the Currency Converter API endpoint.

This script tests the /api/v1/currency_converter endpoint with various inputs.
"""

import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/currency_converter"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin"


def test_usd_to_eur():
    """Test USD to EUR conversion"""
    print("\n=== Test 1: Convert 100 USD to EUR ===")

    data = {
        "amount": 100,
        "from_currency": "USD",
        "to_currency": "EUR"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        print(f"\n100 USD = {result.get('converted_amount')} EUR")
        print(f"Exchange rate: {result.get('rate')}")

    return response.status_code == 200


def test_eur_to_rub():
    """Test EUR to RUB conversion"""
    print("\n=== Test 2: Convert 50 EUR to RUB ===")

    data = {
        "amount": 50,
        "from_currency": "EUR",
        "to_currency": "RUB"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        print(f"\n50 EUR = {result.get('converted_amount')} RUB")
        print(f"Exchange rate: {result.get('rate')}")

    return response.status_code == 200


def test_same_currency():
    """Test conversion with same currency (rate should be 1.0)"""
    print("\n=== Test 3: Convert USD to USD (should return same amount) ===")

    data = {
        "amount": 100,
        "from_currency": "USD",
        "to_currency": "USD"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    return response.status_code == 200 and result.get('rate', 0) == 1.0


def test_invalid_currency():
    """Test with invalid currency code"""
    print("\n=== Test 4: Invalid currency code (should return error) ===")

    data = {
        "amount": 100,
        "from_currency": "INVALID",
        "to_currency": "EUR"
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 422


def test_missing_fields():
    """Test with missing required fields"""
    print("\n=== Test 5: Missing required fields (should return error) ===")

    data = {
        "amount": 100
    }

    response = requests.post(API_URL, json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 422


def main():
    """Run all tests"""
    print("=" * 80)
    print("Currency Converter API - Test Suite")
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
    results.append(("USD to EUR conversion", test_usd_to_eur()))
    results.append(("EUR to RUB conversion", test_eur_to_rub()))
    results.append(("Same currency conversion", test_same_currency()))
    results.append(("Invalid currency code", test_invalid_currency()))
    results.append(("Missing required fields", test_missing_fields()))

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
