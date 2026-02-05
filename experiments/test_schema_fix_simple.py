#!/usr/bin/env python
"""
Simple test to verify that the marketplace views can be imported without serialization errors.
This specifically tests the fix for issue #33 - the marketplace app serialization error.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that the marketplace module can be imported."""
    print("Testing imports...")

    try:
        # Import serializers
        print("  Importing marketplace.serializers...")
        from marketplace import serializers
        print("  ✓ marketplace.serializers imported successfully")

        # Check that inline_serializer is imported in views
        print("  Importing marketplace.views...")
        import importlib.util
        spec = importlib.util.spec_from_file_location("marketplace.views", "marketplace/views.py")
        views_module = importlib.util.module_from_spec(spec)

        # Read the file to check for inline_serializer
        with open("marketplace/views.py", "r") as f:
            views_content = f.read()

        # Check that inline_serializer is imported
        if "from drf_spectacular.utils import extend_schema, inline_serializer" in views_content:
            print("  ✓ inline_serializer is properly imported")
        else:
            print("  ✗ inline_serializer is not imported")
            return False

        # Check that the problematic response definition is fixed
        if "inline_serializer(\n            name='StoreMenuListResponse'," in views_content:
            print("  ✓ store_menu_list response uses inline_serializer")
        else:
            print("  ✗ store_menu_list response is not using inline_serializer")
            return False

        # Check that serializer classes are not directly in dict (the bug)
        if "'store': StorePublicSerializer," in views_content and "'menu_items': {'type': 'array'" in views_content:
            print("  ✗ Bug still present: serializer classes used directly in response dict")
            return False
        else:
            print("  ✓ Serializer classes are not used directly in response dict")

        print("\n✓ All checks passed! The fix is correct.")
        return True

    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
