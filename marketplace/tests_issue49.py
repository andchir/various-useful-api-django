"""
Test for issue #49 - store_update should not delete logo when empty/null is sent.
"""
import json
import io
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from marketplace.models import StoreModel


class StoreUpdateImagePreservationTestCase(TestCase):
    """Test cases for issue #49 - image preservation during updates"""

    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """Helper method to create a test image"""
        file = io.BytesIO()
        image = Image.new('RGB', size, color='red')
        image.save(file, format)
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type=f'image/{format.lower()}')

    def test_store_update_preserves_logo_when_not_included(self):
        """Test that updating store without logo field preserves existing logo"""
        # Step 1: Create a store with a logo
        logo = self.create_test_image()
        data = {
            'name': 'Test Store',
            'description': 'Test Description',
            'currency': 'USD',
            'logo': logo
        }
        response = self.client.post('/api/v1/store/create', data)
        self.assertEqual(response.status_code, 201)

        store_data = json.loads(response.content)
        write_uuid = store_data['write_uuid']
        original_logo_url = store_data['logo']
        self.assertIsNotNone(original_logo_url)

        # Verify logo exists in database
        store = StoreModel.objects.get(write_uuid=write_uuid)
        self.assertTrue(store.logo)

        # Step 2: Update store without sending logo field
        update_data = {
            'name': 'Updated Store Name',
            'description': 'Updated Description'
        }
        response = self.client.put(
            f'/api/v1/store/update/{write_uuid}',
            json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        updated_data = json.loads(response.content)

        # Verify logo is preserved
        store.refresh_from_db()
        self.assertTrue(store.logo, "Logo should be preserved when not included in update")
        self.assertIsNotNone(updated_data.get('logo'), "Logo URL should be returned in response")

    def test_store_update_preserves_logo_when_null_sent(self):
        """Test that updating store with null logo preserves existing logo"""
        # Step 1: Create a store with a logo
        logo = self.create_test_image()
        data = {
            'name': 'Test Store',
            'description': 'Test Description',
            'currency': 'USD',
            'logo': logo
        }
        response = self.client.post('/api/v1/store/create', data)
        self.assertEqual(response.status_code, 201)

        store_data = json.loads(response.content)
        write_uuid = store_data['write_uuid']
        original_logo_url = store_data['logo']
        self.assertIsNotNone(original_logo_url)

        # Verify logo exists in database
        store = StoreModel.objects.get(write_uuid=write_uuid)
        original_logo_name = store.logo.name
        self.assertTrue(store.logo)

        # Step 2: Update store with explicit null logo
        update_data = {
            'name': 'Updated Again',
            'logo': None
        }
        response = self.client.put(
            f'/api/v1/store/update/{write_uuid}',
            json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        updated_data = json.loads(response.content)

        # Verify logo is still preserved (not deleted)
        store.refresh_from_db()
        self.assertTrue(store.logo, "Logo should be preserved when null is sent")
        self.assertEqual(store.logo.name, original_logo_name, "Logo should remain unchanged")
        self.assertIsNotNone(updated_data.get('logo'), "Logo URL should be returned in response")

    def test_store_update_replaces_logo_when_new_image_sent(self):
        """Test that updating store with new logo replaces the old one"""
        # Step 1: Create a store with a logo
        logo = self.create_test_image()
        data = {
            'name': 'Test Store',
            'description': 'Test Description',
            'currency': 'USD',
            'logo': logo
        }
        response = self.client.post('/api/v1/store/create', data)
        self.assertEqual(response.status_code, 201)

        store_data = json.loads(response.content)
        write_uuid = store_data['write_uuid']

        # Verify logo exists in database
        store = StoreModel.objects.get(write_uuid=write_uuid)
        original_logo_name = store.logo.name
        self.assertTrue(store.logo)

        # Step 2: Update store with new logo
        new_logo = self.create_test_image(name='new_logo.jpg')
        data = {
            'name': 'Updated Store',
            'logo': new_logo
        }
        response = self.client.put(
            f'/api/v1/store/update/{write_uuid}',
            data
        )
        self.assertEqual(response.status_code, 200)

        # Verify logo was replaced
        store.refresh_from_db()
        self.assertTrue(store.logo)
        self.assertNotEqual(store.logo.name, original_logo_name, "Logo should be replaced with new image")


class MenuItemUpdateImagePreservationTestCase(TestCase):
    """Test cases for issue #49 - image preservation during menu item updates"""

    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """Helper method to create a test image"""
        file = io.BytesIO()
        image = Image.new('RGB', size, color='red')
        image.save(file, format)
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type=f'image/{format.lower()}')

    def test_menu_item_update_preserves_photo_when_not_included(self):
        """Test that updating menu item without photo field preserves existing photo"""
        # Create a store
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='USD'
        )

        # Create a menu item with photo
        photo = self.create_test_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'photo': photo
        }
        response = self.client.post(
            f'/api/v1/store/{store.write_uuid}/menu/create',
            data
        )
        self.assertEqual(response.status_code, 201)

        menu_item_data = json.loads(response.content)
        product_uuid = menu_item_data['uuid']
        original_photo_url = menu_item_data['photo']
        self.assertIsNotNone(original_photo_url)

        # Update menu item without sending photo field
        update_data = {
            'name': 'Updated Product Name',
            'description': 'Updated Description',
            'price': '79.99'
        }
        response = self.client.put(
            f'/api/v1/store/{store.write_uuid}/menu/{product_uuid}/update',
            json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        updated_data = json.loads(response.content)

        # Verify photo is preserved
        from marketplace.models import StoreProductModel
        menu_item = StoreProductModel.objects.get(uuid=product_uuid)
        self.assertTrue(menu_item.photo, "Photo should be preserved when not included in update")
        self.assertIsNotNone(updated_data.get('photo'), "Photo URL should be returned in response")

    def test_menu_item_update_preserves_photo_when_null_sent(self):
        """Test that updating menu item with null photo preserves existing photo"""
        # Create a store
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='USD'
        )

        # Create a menu item with photo
        photo = self.create_test_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'photo': photo
        }
        response = self.client.post(
            f'/api/v1/store/{store.write_uuid}/menu/create',
            data
        )
        self.assertEqual(response.status_code, 201)

        menu_item_data = json.loads(response.content)
        product_uuid = menu_item_data['uuid']

        # Verify photo exists in database
        from marketplace.models import StoreProductModel
        menu_item = StoreProductModel.objects.get(uuid=product_uuid)
        original_photo_name = menu_item.photo.name
        self.assertTrue(menu_item.photo)

        # Update menu item with explicit null photo
        update_data = {
            'name': 'Updated Product',
            'photo': None
        }
        response = self.client.put(
            f'/api/v1/store/{store.write_uuid}/menu/{product_uuid}/update',
            json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        updated_data = json.loads(response.content)

        # Verify photo is still preserved (not deleted)
        menu_item.refresh_from_db()
        self.assertTrue(menu_item.photo, "Photo should be preserved when null is sent")
        self.assertEqual(menu_item.photo.name, original_photo_name, "Photo should remain unchanged")
        self.assertIsNotNone(updated_data.get('photo'), "Photo URL should be returned in response")
