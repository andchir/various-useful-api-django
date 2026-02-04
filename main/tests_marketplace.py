"""
Unit tests for Marketplace API
"""
import json
import io
from decimal import Decimal
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from main.models import StoreModel, MenuItemModel, CartModel, CartItemModel


class MarketplaceAPITestCase(TestCase):
    """Test cases for Marketplace API"""

    def setUp(self):
        """Set up test client and test data"""
        self.client = Client()

    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """Helper method to create a test image"""
        file = io.BytesIO()
        image = Image.new('RGB', size, color='red')
        image.save(file, format)
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type=f'image/{format.lower()}')

    def test_store_create(self):
        """Test creating a store"""
        data = {
            'name': 'Test Store',
            'description': 'Test Description',
            'currency': 'руб.'
        }
        response = self.client.post('/api/v1/store/create', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Test Store')
        self.assertEqual(response_data['currency'], 'руб.')
        self.assertIn('read_uuid', response_data)
        self.assertIn('write_uuid', response_data)

    def test_store_create_with_logo(self):
        """Test creating a store with logo"""
        logo = self.create_test_image()
        data = {
            'name': 'Store with Logo',
            'description': 'Test Description',
            'currency': 'USD',
            'logo': logo
        }
        response = self.client.post('/api/v1/store/create', data)
        self.assertEqual(response.status_code, 201)

    def test_store_create_with_oversized_logo(self):
        """Test creating a store with logo exceeding 5MB (should fail)"""
        # Create a large image (will be rejected due to 5MB limit)
        large_logo = self.create_test_image(name='large.jpg', size=(5000, 5000))
        data = {
            'name': 'Store with Large Logo',
            'description': 'Test Description',
            'currency': 'EUR',
            'logo': large_logo
        }
        response = self.client.post('/api/v1/store/create', data)
        # Should fail validation
        self.assertIn(response.status_code, [400, 422])

    def test_store_update(self):
        """Test updating a store"""
        # Create a store first
        store = StoreModel.objects.create(
            name='Original Name',
            description='Original Description',
            currency='руб.'
        )

        update_data = {
            'name': 'Updated Name',
            'description': 'Updated Description',
            'currency': 'USD'
        }
        response = self.client.put(
            f'/api/v1/store/update/{store.write_uuid}',
            json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Updated Name')
        self.assertEqual(response_data['currency'], 'USD')

    def test_store_update_with_invalid_uuid(self):
        """Test updating a store with invalid write_uuid"""
        import uuid
        invalid_uuid = uuid.uuid4()

        update_data = {
            'name': 'Updated Name'
        }
        response = self.client.put(
            f'/api/v1/store/update/{invalid_uuid}',
            json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_menu_item_create(self):
        """Test creating a menu item"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        photo = self.create_test_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Product Description',
            'price': '99.99',
            'photo': photo
        }
        response = self.client.post(
            f'/api/v1/store/{store.write_uuid}/menu/create',
            data
        )
        self.assertEqual(response.status_code, 201)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Test Product')
        self.assertEqual(float(response_data['price']), 99.99)
        self.assertIn('uuid', response_data)

    def test_menu_item_create_without_photo(self):
        """Test creating a menu item without photo"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        data = {
            'name': 'Product Without Photo',
            'description': 'Test Product Description',
            'price': '49.99'
        }
        response = self.client.post(
            f'/api/v1/store/{store.write_uuid}/menu/create',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

    def test_menu_item_create_with_invalid_write_uuid(self):
        """Test creating a menu item with invalid write_uuid"""
        import uuid
        invalid_uuid = uuid.uuid4()

        data = {
            'name': 'Test Product',
            'price': '99.99'
        }
        response = self.client.post(
            f'/api/v1/store/{invalid_uuid}/menu/create',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_store_menu_list(self):
        """Test getting store menu list"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        # Create some menu items
        MenuItemModel.objects.create(
            store=store,
            name='Product 1',
            description='Description 1',
            price=Decimal('10.00')
        )
        MenuItemModel.objects.create(
            store=store,
            name='Product 2',
            description='Description 2',
            price=Decimal('20.00')
        )

        response = self.client.get(f'/api/v1/store/{store.read_uuid}/menu')
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn('store', response_data)
        self.assertIn('menu_items', response_data)
        self.assertEqual(len(response_data['menu_items']), 2)
        # Verify write_uuid is not in store data
        self.assertNotIn('write_uuid', response_data['store'])

    def test_cart_create(self):
        """Test creating a cart"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        response = self.client.post(f'/api/v1/cart/create/{store.read_uuid}')
        self.assertEqual(response.status_code, 201)

        response_data = json.loads(response.content)
        self.assertIn('uuid', response_data)
        self.assertEqual(response_data['store_name'], 'Test Store')
        self.assertEqual(response_data['items'], [])
        self.assertEqual(float(response_data['total_price']), 0.0)

    def test_cart_add_item(self):
        """Test adding an item to cart"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        menu_item = MenuItemModel.objects.create(
            store=store,
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99')
        )

        cart = CartModel.objects.create(store=store)

        data = {
            'menu_item_uuid': str(menu_item.uuid),
            'quantity': 2
        }
        response = self.client.post(
            f'/api/v1/cart/{cart.uuid}/add',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['items']), 1)
        self.assertEqual(response_data['items'][0]['quantity'], 2)
        self.assertEqual(float(response_data['total_price']), 199.98)

    def test_cart_add_item_update_quantity(self):
        """Test updating quantity of existing item in cart"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        menu_item = MenuItemModel.objects.create(
            store=store,
            name='Test Product',
            description='Test Description',
            price=Decimal('50.00')
        )

        cart = CartModel.objects.create(store=store)

        # Add item first time
        data = {
            'menu_item_uuid': str(menu_item.uuid),
            'quantity': 1
        }
        self.client.post(
            f'/api/v1/cart/{cart.uuid}/add',
            json.dumps(data),
            content_type='application/json'
        )

        # Add same item again with different quantity
        data = {
            'menu_item_uuid': str(menu_item.uuid),
            'quantity': 3
        }
        response = self.client.post(
            f'/api/v1/cart/{cart.uuid}/add',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['items']), 1)
        self.assertEqual(response_data['items'][0]['quantity'], 3)
        self.assertEqual(float(response_data['total_price']), 150.00)

    def test_cart_add_item_from_different_store(self):
        """Test adding item from different store to cart (should fail)"""
        store1 = StoreModel.objects.create(
            name='Store 1',
            description='Description 1',
            currency='руб.'
        )

        store2 = StoreModel.objects.create(
            name='Store 2',
            description='Description 2',
            currency='руб.'
        )

        menu_item = MenuItemModel.objects.create(
            store=store2,
            name='Product from Store 2',
            description='Test Description',
            price=Decimal('50.00')
        )

        cart = CartModel.objects.create(store=store1)

        data = {
            'menu_item_uuid': str(menu_item.uuid),
            'quantity': 1
        }
        response = self.client.post(
            f'/api/v1/cart/{cart.uuid}/add',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_cart_remove_item(self):
        """Test removing an item from cart"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        menu_item = MenuItemModel.objects.create(
            store=store,
            name='Test Product',
            description='Test Description',
            price=Decimal('50.00')
        )

        cart = CartModel.objects.create(store=store)
        CartItemModel.objects.create(
            cart=cart,
            menu_item=menu_item,
            quantity=2
        )

        data = {
            'menu_item_uuid': str(menu_item.uuid)
        }
        response = self.client.post(
            f'/api/v1/cart/{cart.uuid}/remove',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['items']), 0)
        self.assertEqual(float(response_data['total_price']), 0.0)

    def test_cart_remove_nonexistent_item(self):
        """Test removing an item that's not in cart"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        menu_item = MenuItemModel.objects.create(
            store=store,
            name='Test Product',
            description='Test Description',
            price=Decimal('50.00')
        )

        cart = CartModel.objects.create(store=store)

        data = {
            'menu_item_uuid': str(menu_item.uuid)
        }
        response = self.client.post(
            f'/api/v1/cart/{cart.uuid}/remove',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_cart_multiple_items_total_price(self):
        """Test total price calculation with multiple items"""
        store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )

        item1 = MenuItemModel.objects.create(
            store=store,
            name='Product 1',
            price=Decimal('10.50')
        )
        item2 = MenuItemModel.objects.create(
            store=store,
            name='Product 2',
            price=Decimal('25.75')
        )

        cart = CartModel.objects.create(store=store)

        # Add first item
        data = {
            'menu_item_uuid': str(item1.uuid),
            'quantity': 2
        }
        self.client.post(
            f'/api/v1/cart/{cart.uuid}/add',
            json.dumps(data),
            content_type='application/json'
        )

        # Add second item
        data = {
            'menu_item_uuid': str(item2.uuid),
            'quantity': 3
        }
        response = self.client.post(
            f'/api/v1/cart/{cart.uuid}/add',
            json.dumps(data),
            content_type='application/json'
        )

        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['items']), 2)
        # 2 * 10.50 + 3 * 25.75 = 21.00 + 77.25 = 98.25
        self.assertEqual(float(response_data['total_price']), 98.25)
