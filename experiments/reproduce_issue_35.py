"""
Reproduce the exact error from issue #35:
Error: unsupported operand type(s) for /: 'str' and 'int'

This happens when size parameter is passed as string "30" instead of int 30
"""
import sys
import os
import django

# Add the project root to Python path
sys.path.insert(0, '/tmp/gh-issue-solver-1770330661591')

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from main.views import css_triangle_generator
from django.test import RequestFactory
from django.contrib.auth.models import User
import json

print("=" * 80)
print("Reproducing Issue #35: CSS Triangle Generator Type Error")
print("=" * 80)

# Create a test user
try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(username='testuser', password='testpass')

# Create request factory
factory = RequestFactory()

# Test case from issue #35 - exactly as reported
test_data = {
    "direction": "top",
    "color": "#B70B0B",
    "size": 30
}

print(f"\nTest Input (as in issue):")
print(json.dumps(test_data, indent=2))

# Create POST request
request = factory.post('/api/v1/css_triangle_generator',
                      data=json.dumps(test_data),
                      content_type='application/json')
request.user = user

print("\nCalling css_triangle_generator()...")

# Call the view
response = css_triangle_generator(request)

# Parse response
response_data = json.loads(response.content.decode('utf-8'))

print(f"\nResponse Status: {response.status_code}")
print(f"Response Data:")
print(json.dumps(response_data, indent=2))

if response.status_code == 200 and response_data.get('success'):
    print("\n✓ SUCCESS - API works correctly!")
    print("\nGenerated CSS:")
    print(response_data.get('css_code'))
else:
    print("\n✗ FAILED - Error occurred as expected:")
    print(f"Message: {response_data.get('message')}")

print("\n" + "=" * 80)
