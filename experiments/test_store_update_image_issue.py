"""
Test to demonstrate issue #49 - store_update deletes logo when empty/null is sent.
The expected behavior is to preserve the existing logo if no new logo is provided.
"""
import json
import io
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from marketplace.models import StoreModel


def create_test_image(name='test.jpg', size=(100, 100), format='JPEG'):
    """Helper to create a test image"""
    file = io.BytesIO()
    image = Image.new('RGB', size, color='red')
    image.save(file, format)
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type=f'image/{format.lower()}')


def test_store_update_preserves_logo_when_null():
    """Test that updating store with null logo preserves existing logo"""
    client = Client()

    # Step 1: Create a store with a logo
    print("Step 1: Creating store with logo...")
    logo = create_test_image()
    data = {
        'name': 'Test Store',
        'description': 'Test Description',
        'currency': 'USD',
        'logo': logo
    }
    response = client.post('/api/v1/store/create', data)
    assert response.status_code == 201, f"Store creation failed: {response.content}"

    store_data = json.loads(response.content)
    write_uuid = store_data['write_uuid']
    original_logo_url = store_data['logo']

    print(f"Store created successfully")
    print(f"Original logo URL: {original_logo_url}")
    print(f"Write UUID: {write_uuid}")

    # Verify logo exists in database
    store = StoreModel.objects.get(write_uuid=write_uuid)
    print(f"Logo field in DB: {store.logo}")
    assert store.logo, "Logo should be saved in database"

    # Step 2: Update store without sending logo field (JSON request)
    print("\nStep 2: Updating store without logo field (JSON request)...")
    update_data = {
        'name': 'Updated Store Name',
        'description': 'Updated Description'
    }
    response = client.put(
        f'/api/v1/store/update/{write_uuid}',
        json.dumps(update_data),
        content_type='application/json'
    )
    assert response.status_code == 200, f"Store update failed: {response.content}"

    updated_data = json.loads(response.content)
    print(f"Updated logo URL: {updated_data.get('logo')}")

    # Verify logo is preserved
    store.refresh_from_db()
    print(f"Logo field in DB after update: {store.logo}")

    if store.logo and updated_data.get('logo'):
        print("✓ PASS: Logo preserved when not included in update")
    else:
        print("✗ FAIL: Logo was deleted when not included in update")
        print(f"  Expected logo to be preserved, but got: {store.logo}")

    # Step 3: Update store with explicit null logo
    print("\nStep 3: Updating store with explicit null logo...")
    update_data_with_null = {
        'name': 'Updated Again',
        'logo': None
    }
    response = client.put(
        f'/api/v1/store/update/{write_uuid}',
        json.dumps(update_data_with_null),
        content_type='application/json'
    )
    assert response.status_code == 200, f"Store update failed: {response.content}"

    updated_data = json.loads(response.content)
    print(f"Updated logo URL: {updated_data.get('logo')}")

    # Verify logo is still preserved (not deleted)
    store.refresh_from_db()
    print(f"Logo field in DB after null update: {store.logo}")

    if store.logo and updated_data.get('logo'):
        print("✓ PASS: Logo preserved when null is sent")
    else:
        print("✗ FAIL: Logo was deleted when null was sent")
        print(f"  Expected logo to be preserved, but got: {store.logo}")
        print(f"  This is the BUG we need to fix!")

    # Clean up
    store.delete()
    print("\nTest completed")


if __name__ == '__main__':
    test_store_update_preserves_logo_when_null()
