"""
Test script for CSS triangle generator API
"""
import sys
import os
import django

# Add the project root to Python path
sys.path.insert(0, '/tmp/gh-issue-solver-1769984234564')

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from main.views import css_triangle_generator
from django.test import RequestFactory
from django.contrib.auth.models import User
import json

# Create a test user
try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(username='testuser', password='testpass')

# Create request factory
factory = RequestFactory()

# Test cases based on the issue requirements
test_cases = [
    {
        'name': 'Top triangle (default)',
        'data': {'direction': 'top', 'color': '#B70B0B', 'size': 30},
        'expected_lines': [
            'border-right: 15px solid transparent;',
            'border-left: 15px solid transparent;',
            'border-bottom: 26px solid #b70b0b;',
            'border-top: 0;'
        ]
    },
    {
        'name': 'Right triangle',
        'data': {'direction': 'right', 'color': '#B70B0B', 'size': 30},
        'expected_lines': [
            'border-top: 15px solid transparent;',
            'border-bottom: 15px solid transparent;',
            'border-left: 26px solid #b70b0b;',
            'border-right: 0;'
        ]
    },
    {
        'name': 'Bottom triangle',
        'data': {'direction': 'bottom', 'color': '#B70B0B', 'size': 30},
        'expected_lines': [
            'border-right: 15px solid transparent;',
            'border-left: 15px solid transparent;',
            'border-top: 26px solid #b70b0b;',
            'border-bottom: 0;'
        ]
    },
    {
        'name': 'Left triangle',
        'data': {'direction': 'left', 'color': '#B70B0B', 'size': 30},
        'expected_lines': [
            'border-top: 15px solid transparent;',
            'border-bottom: 15px solid transparent;',
            'border-right: 26px solid #b70b0b;',
            'border-left: 0;'
        ]
    },
    {
        'name': 'Default parameters',
        'data': {},
        'expected_lines': [
            'border-right: 15px solid transparent;',
            'border-left: 15px solid transparent;',
            'border-bottom: 26px solid #b70b0b;',
            'border-top: 0;'
        ]
    }
]

print("Testing CSS Triangle Generator API\n")
print("=" * 80)

all_passed = True

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Input: {test['data']}")

    # Create POST request
    request = factory.post('/api/v1/css_triangle_generator',
                          data=json.dumps(test['data']),
                          content_type='application/json')
    request.user = user

    # Call the view
    response = css_triangle_generator(request)

    # Parse response
    response_data = json.loads(response.content.decode('utf-8'))

    # Check if successful
    if response.status_code == 200 and response_data.get('success'):
        css_code = response_data.get('css_code', '')
        print(f"Status: ✓ SUCCESS")
        print(f"Response:\n{css_code}")

        # Validate expected lines are in the output
        missing_lines = []
        for expected_line in test['expected_lines']:
            if expected_line not in css_code:
                missing_lines.append(expected_line)

        if missing_lines:
            print(f"✗ VALIDATION FAILED: Missing expected lines:")
            for line in missing_lines:
                print(f"  - {line}")
            all_passed = False
        else:
            print("✓ All expected lines present")
    else:
        print(f"✗ FAILED: {response_data}")
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✓ All tests PASSED!")
else:
    print("✗ Some tests FAILED")
    sys.exit(1)
