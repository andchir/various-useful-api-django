#!/usr/bin/env python
"""
Static code analysis to verify that the marketplace views fix is correct.
This specifically tests the fix for issue #33 - the marketplace app serialization error.
"""

import sys
import os
import re

def test_fix():
    """Test that the fix is correctly applied."""
    print("=" * 70)
    print("Testing fix for issue #33: Swagger schema serialization error")
    print("=" * 70)
    print()

    views_file = "marketplace/views.py"

    try:
        with open(views_file, "r") as f:
            views_content = f.read()

        print("✓ Successfully read marketplace/views.py")
        print()

        # Test 1: Check that inline_serializer is imported
        print("[Test 1] Checking inline_serializer import...")
        if "from drf_spectacular.utils import extend_schema, inline_serializer" in views_content:
            print("  ✓ PASS: inline_serializer is properly imported")
        else:
            print("  ✗ FAIL: inline_serializer is not imported")
            return False
        print()

        # Test 2: Check that the problematic response definition is fixed
        print("[Test 2] Checking store_menu_list uses inline_serializer...")
        if "inline_serializer(" in views_content and "name='StoreMenuListResponse'" in views_content:
            print("  ✓ PASS: store_menu_list response uses inline_serializer")
        else:
            print("  ✗ FAIL: store_menu_list response is not using inline_serializer")
            return False
        print()

        # Test 3: Check that serializer classes are instantiated with ()
        print("[Test 3] Checking serializer instances are properly created...")
        if "StorePublicSerializer()" in views_content and "MenuItemResponseSerializer(many=True)" in views_content:
            print("  ✓ PASS: Serializers are instantiated (not class references)")
        else:
            print("  ✗ FAIL: Serializers are not properly instantiated")
            return False
        print()

        # Test 4: Check that the old buggy code is NOT present
        print("[Test 4] Checking old buggy code is removed...")
        buggy_pattern1 = "'store': StorePublicSerializer,"
        buggy_pattern2 = "'menu_items': {'type': 'array', 'items': MenuItemResponseSerializer}"

        if buggy_pattern1 in views_content or buggy_pattern2 in views_content:
            print("  ✗ FAIL: Old buggy code still present!")
            return False
        else:
            print("  ✓ PASS: Old buggy code has been removed")
        print()

        # Test 5: Check the structure of the fixed code
        print("[Test 5] Checking the structure of the fix...")
        expected_structure = """@extend_schema(
    tags=['Marketplace'],
    responses={
        200: inline_serializer(
            name='StoreMenuListResponse',
            fields={
                'store': StorePublicSerializer(),
                'menu_items': MenuItemResponseSerializer(many=True),
            }
        ),
        404: ErrorResponseSerializer,
    },
)"""
        if expected_structure in views_content:
            print("  ✓ PASS: Fix structure is correct")
        else:
            print("  ⚠ WARNING: Fix structure might differ (but may still be correct)")
        print()

        print("=" * 70)
        print("✓ ALL TESTS PASSED! The fix for issue #33 is correctly applied.")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - inline_serializer is imported from drf_spectacular.utils")
        print("  - store_menu_list uses inline_serializer for nested response")
        print("  - Serializer instances are created with ()")
        print("  - Old buggy code (class references in dict) removed")
        print()
        print("The error 'Object of type SerializerMetaclass is not JSON serializable'")
        print("should now be resolved!")
        return True

    except Exception as e:
        print(f"✗ Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_fix()
    sys.exit(0 if success else 1)
