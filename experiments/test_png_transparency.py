"""
Test script to verify PNG transparency preservation with django-resized.

This script tests that ResizedImageField with force_format='PNG' preserves
the alpha channel (transparency) in PNG images.
"""

import os
import sys
from io import BytesIO
from PIL import Image

# Add parent directory to path to import django settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from marketplace.models import StoreModel, StoreProductModel


def create_test_png_with_transparency(size=(1000, 1000)):
    """
    Create a test PNG image with transparency (alpha channel).

    Returns:
        BytesIO: Image file in memory with RGBA mode (transparent background)
    """
    # Create RGBA image (with alpha channel for transparency)
    img = Image.new('RGBA', size, (0, 0, 0, 0))  # Transparent background

    # Draw a semi-transparent red circle in the center
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    center_x, center_y = size[0] // 2, size[1] // 2
    radius = min(size) // 3

    # Draw circle with semi-transparent red (RGBA)
    draw.ellipse(
        [(center_x - radius, center_y - radius),
         (center_x + radius, center_y + radius)],
        fill=(255, 0, 0, 128)  # Red with 50% transparency
    )

    # Save to BytesIO
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    return img_io


def test_store_logo_transparency():
    """Test that StoreModel logo field preserves PNG transparency."""
    print("\n=== Testing StoreModel logo transparency ===")

    # Create test PNG with transparency
    test_image = create_test_png_with_transparency((1000, 1000))

    # Create a store with the test image
    store = StoreModel.objects.create(
        name="Test Store for PNG Transparency",
        description="Testing PNG transparency preservation",
        currency="USD"
    )

    # Upload the image
    store.logo.save(
        'test_logo_transparency.png',
        SimpleUploadedFile(
            'test_logo_transparency.png',
            test_image.read(),
            content_type='image/png'
        )
    )
    store.save()

    # Read the saved image and check if it has alpha channel
    saved_image = Image.open(store.logo.path)

    print(f"Original mode: RGBA (with transparency)")
    print(f"Saved image mode: {saved_image.mode}")
    print(f"Saved image format: {saved_image.format}")
    print(f"Saved image size: {saved_image.size}")
    print(f"Has alpha channel: {saved_image.mode in ('RGBA', 'LA', 'PA')}")

    # Verify the image has alpha channel
    assert saved_image.mode == 'RGBA', f"Expected RGBA mode, got {saved_image.mode}"
    assert saved_image.format == 'PNG', f"Expected PNG format, got {saved_image.format}"

    # Check that the image is resized to max 800x800
    assert max(saved_image.size) <= 800, f"Image not properly resized: {saved_image.size}"

    print("✅ StoreModel logo preserves PNG transparency!")

    # Cleanup
    store.delete()
    return True


def test_product_photo_transparency():
    """Test that StoreProductModel photo field preserves PNG transparency."""
    print("\n=== Testing StoreProductModel photo transparency ===")

    # Create test PNG with transparency
    test_image = create_test_png_with_transparency((2000, 1500))

    # Create a store first
    store = StoreModel.objects.create(
        name="Test Store for Product Photos",
        description="Testing product photo transparency",
        currency="EUR"
    )

    # Create a product with the test image
    product = StoreProductModel.objects.create(
        store=store,
        name="Test Product with Transparent PNG",
        description="Testing PNG transparency",
        price=10.99
    )

    # Upload the image
    product.photo.save(
        'test_product_transparency.png',
        SimpleUploadedFile(
            'test_product_transparency.png',
            test_image.read(),
            content_type='image/png'
        )
    )
    product.save()

    # Read the saved image and check if it has alpha channel
    saved_image = Image.open(product.photo.path)

    print(f"Original mode: RGBA (with transparency)")
    print(f"Saved image mode: {saved_image.mode}")
    print(f"Saved image format: {saved_image.format}")
    print(f"Saved image size: {saved_image.size}")
    print(f"Has alpha channel: {saved_image.mode in ('RGBA', 'LA', 'PA')}")

    # Verify the image has alpha channel
    assert saved_image.mode == 'RGBA', f"Expected RGBA mode, got {saved_image.mode}"
    assert saved_image.format == 'PNG', f"Expected PNG format, got {saved_image.format}"

    # Check that the image is resized to max 1920x1080
    assert max(saved_image.size) <= 1920, f"Image not properly resized: {saved_image.size}"

    print("✅ StoreProductModel photo preserves PNG transparency!")

    # Cleanup
    product.delete()
    store.delete()
    return True


def test_jpeg_upload_still_works():
    """Test that JPEG uploads still work (should be converted to PNG)."""
    print("\n=== Testing JPEG upload conversion ===")

    # Create test JPEG image
    img = Image.new('RGB', (1000, 1000), (255, 0, 0))  # Red image
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)

    # Create a store with JPEG image
    store = StoreModel.objects.create(
        name="Test Store for JPEG",
        description="Testing JPEG upload",
        currency="USD"
    )

    # Upload the JPEG
    store.logo.save(
        'test_logo.jpg',
        SimpleUploadedFile(
            'test_logo.jpg',
            img_io.read(),
            content_type='image/jpeg'
        )
    )
    store.save()

    # Read the saved image
    saved_image = Image.open(store.logo.path)

    print(f"Original format: JPEG")
    print(f"Saved image mode: {saved_image.mode}")
    print(f"Saved image format: {saved_image.format}")

    # With force_format='PNG', JPEG should be converted to PNG
    assert saved_image.format == 'PNG', f"Expected PNG format, got {saved_image.format}"

    print("✅ JPEG uploads are converted to PNG as expected!")

    # Cleanup
    store.delete()
    return True


if __name__ == '__main__':
    try:
        print("Testing PNG Transparency Support in django-resized")
        print("=" * 60)

        # Run all tests
        test_store_logo_transparency()
        test_product_photo_transparency()
        test_jpeg_upload_still_works()

        print("\n" + "=" * 60)
        print("🎉 All tests passed! PNG transparency is preserved.")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
