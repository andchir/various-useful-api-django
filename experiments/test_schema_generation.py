#!/usr/bin/env python
"""
Test script to verify that the OpenAPI schema can be generated without errors.
This specifically tests the fix for issue #33 - the marketplace app serialization error.
"""

import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema
import json

def test_schema_generation():
    """Test that the schema can be generated without errors."""
    print("Testing OpenAPI schema generation...")

    try:
        # Create schema generator
        generator = SchemaGenerator()

        # Generate the schema
        print("Generating schema...")
        schema = generator.get_schema()

        # Try to serialize the schema to JSON (this is where the error occurred)
        print("Serializing schema to JSON...")
        schema_json = json.dumps(schema, indent=2)

        # Validate the schema
        print("Validating schema...")
        validate_schema(schema)

        print(f"\n✓ Schema generated successfully!")
        print(f"✓ Schema size: {len(schema_json)} bytes")
        print(f"✓ Number of paths: {len(schema.get('paths', {}))}")

        # Check if marketplace endpoints are present
        marketplace_paths = [path for path in schema.get('paths', {}).keys() if 'marketplace' in path.lower() or 'store' in path.lower()]
        print(f"✓ Marketplace endpoints found: {len(marketplace_paths)}")
        if marketplace_paths:
            print("  Marketplace paths:")
            for path in marketplace_paths:
                print(f"    - {path}")

        return True

    except Exception as e:
        print(f"\n✗ Error generating schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_schema_generation()
    sys.exit(0 if success else 1)
