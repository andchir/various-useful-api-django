"""
Experiment script to test full URL serialization for marketplace images.
This script tests the serializer logic without requiring a full database setup.
"""
import sys
import os
from unittest.mock import Mock, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

def test_logo_url_serialization():
    """Test that logo URLs are properly serialized to full URLs"""
    from marketplace.serializers import StoreResponseSerializer

    # Create mock store object
    mock_store = Mock()
    mock_store.id = 1
    mock_store.name = "Test Store"
    mock_store.description = "Test Description"
    mock_store.currency = "USD"
    mock_store.date_created = "2025-01-01T00:00:00Z"
    mock_store.date_updated = "2025-01-01T00:00:00Z"

    # Mock logo field
    mock_logo = Mock()
    mock_logo.url = "/media/stores/logos/2025/01/01/test.jpg"
    mock_store.logo = mock_logo

    # Mock read/write UUIDs
    mock_store.read_uuid = "12345678-1234-1234-1234-123456789012"
    mock_store.write_uuid = "87654321-4321-4321-4321-210987654321"

    # Create mock request
    mock_request = Mock()
    mock_request.build_absolute_uri = lambda url: f"http://testserver{url}"

    # Serialize with request context
    serializer = StoreResponseSerializer(mock_store, context={'request': mock_request})
    data = serializer.data

    print("✅ Test: Store logo URL serialization")
    print(f"   Original URL: {mock_logo.url}")
    print(f"   Serialized URL: {data['logo']}")

    # Verify it's a full URL
    assert data['logo'].startswith('http://'), f"Expected full URL, got: {data['logo']}"
    assert 'testserver' in data['logo'], f"Expected domain in URL, got: {data['logo']}"
    assert mock_logo.url in data['logo'], f"Expected original path in URL, got: {data['logo']}"

    print("   ✓ Logo URL is absolute and contains domain\n")

    # Test without request context (should still return the URL path)
    serializer_no_context = StoreResponseSerializer(mock_store, context={})
    data_no_context = serializer_no_context.data
    print("✅ Test: Store logo URL without request context")
    print(f"   Serialized URL: {data_no_context['logo']}")
    assert data_no_context['logo'] == mock_logo.url
    print("   ✓ Returns relative URL when no request context\n")

    # Test with None logo
    mock_store.logo = None
    serializer_null = StoreResponseSerializer(mock_store, context={'request': mock_request})
    data_null = serializer_null.data
    print("✅ Test: Store with no logo")
    print(f"   Serialized URL: {data_null['logo']}")
    assert data_null['logo'] is None
    print("   ✓ Returns None when no logo\n")


def test_menu_item_photo_serialization():
    """Test that menu item photo URLs are properly serialized to full URLs"""
    from marketplace.serializers import MenuItemResponseSerializer

    # Create mock menu item
    mock_item = Mock()
    mock_item.id = 1
    mock_item.uuid = "abcdef12-3456-7890-abcd-ef1234567890"
    mock_item.name = "Test Product"
    mock_item.description = "Test Description"
    mock_item.price = 99.99
    mock_item.date_created = "2025-01-01T00:00:00Z"
    mock_item.date_updated = "2025-01-01T00:00:00Z"

    # Mock store
    mock_store = Mock()
    mock_store.name = "Test Store"
    mock_store.currency = "USD"
    mock_item.store = mock_store

    # Mock photo field
    mock_photo = Mock()
    mock_photo.url = "/media/stores/menu_items/2025/01/01/product.jpg"
    mock_item.photo = mock_photo

    # Create mock request
    mock_request = Mock()
    mock_request.build_absolute_uri = lambda url: f"http://testserver{url}"

    # Serialize with request context
    serializer = MenuItemResponseSerializer(mock_item, context={'request': mock_request})
    data = serializer.data

    print("✅ Test: Menu item photo URL serialization")
    print(f"   Original URL: {mock_photo.url}")
    print(f"   Serialized URL: {data['photo']}")

    # Verify it's a full URL
    assert data['photo'].startswith('http://'), f"Expected full URL, got: {data['photo']}"
    assert 'testserver' in data['photo'], f"Expected domain in URL, got: {data['photo']}"
    assert mock_photo.url in data['photo'], f"Expected original path in URL, got: {data['photo']}"

    print("   ✓ Photo URL is absolute and contains domain\n")


def test_store_public_serializer():
    """Test that public store serializer also returns full URLs"""
    from marketplace.serializers import StorePublicSerializer

    # Create mock store object
    mock_store = Mock()
    mock_store.id = 1
    mock_store.name = "Test Store"
    mock_store.description = "Test Description"
    mock_store.currency = "USD"
    mock_store.read_uuid = "12345678-1234-1234-1234-123456789012"

    # Mock logo field
    mock_logo = Mock()
    mock_logo.url = "/media/stores/logos/2025/01/01/logo.jpg"
    mock_store.logo = mock_logo

    # Create mock request
    mock_request = Mock()
    mock_request.build_absolute_uri = lambda url: f"http://example.com{url}"

    # Serialize with request context
    serializer = StorePublicSerializer(mock_store, context={'request': mock_request})
    data = serializer.data

    print("✅ Test: Public store serializer logo URL")
    print(f"   Original URL: {mock_logo.url}")
    print(f"   Serialized URL: {data['logo']}")

    # Verify it's a full URL
    assert data['logo'].startswith('http://'), f"Expected full URL, got: {data['logo']}"
    assert 'example.com' in data['logo'], f"Expected domain in URL, got: {data['logo']}"

    print("   ✓ Public serializer returns full URLs\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Full URL Serialization for Marketplace Images")
    print("=" * 60)
    print()

    try:
        test_logo_url_serialization()
        test_menu_item_photo_serialization()
        test_store_public_serializer()

        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nConclusion: Image fields now return full absolute URLs with domain")
        print("when serialized with request context in all marketplace serializers.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
