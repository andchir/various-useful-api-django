"""
Tests for marketplace store API endpoints.
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from marketplace.models import StoreModel, StoreProductModel, CartModel, CartItemModel


class StoreAPITestCase(TestCase):
    """Test case for Store API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )
        self.product = StoreProductModel.objects.create(
            store=self.store,
            name='Test Product',
            description='Test Product Description',
            price=Decimal('100.50')
        )
        self.cart = CartModel.objects.create(
            store=self.store,
            status='created'
        )
    
    def test_store_delete_success(self):
        """Test successful store deletion."""
        url = reverse('marketplace_store_delete', kwargs={'write_uuid': self.store.write_uuid})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Store deleted successfully')
        
        # Verify store is deleted
        with self.assertRaises(StoreModel.DoesNotExist):
            StoreModel.objects.get(id=self.store.id)
    
    def test_store_delete_invalid_uuid(self):
        """Test store deletion with invalid write_uuid."""
        invalid_uuid = uuid.uuid4()
        url = reverse('marketplace_store_delete', kwargs={'write_uuid': invalid_uuid})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Store not found or invalid write_uuid')


class MenuItemAPITestCase(TestCase):
    """Test case for Menu Item API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )
        self.product = StoreProductModel.objects.create(
            store=self.store,
            name='Test Product',
            description='Test Product Description',
            price=Decimal('100.50')
        )
    
    def test_menu_item_update_success(self):
        """Test successful menu item update."""
        url = reverse('marketplace_menu_item_update', kwargs={
            'write_uuid': self.store.write_uuid,
            'product_uuid': self.product.uuid
        })
        data = {
            'name': 'Updated Product Name',
            'price': '150.75',
            'description': 'Updated Description'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product Name')
        self.assertEqual(self.product.price, Decimal('150.75'))
        self.assertEqual(self.product.description, 'Updated Description')
    
    def test_menu_item_update_invalid_write_uuid(self):
        """Test menu item update with invalid write_uuid."""
        invalid_write_uuid = uuid.uuid4()
        url = reverse('marketplace_menu_item_update', kwargs={
            'write_uuid': invalid_write_uuid,
            'product_uuid': self.product.uuid
        })
        data = {'name': 'Updated Product Name'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_menu_item_update_invalid_product_uuid(self):
        """Test menu item update with invalid product_uuid."""
        invalid_product_uuid = uuid.uuid4()
        url = reverse('marketplace_menu_item_update', kwargs={
            'write_uuid': self.store.write_uuid,
            'product_uuid': invalid_product_uuid
        })
        data = {'name': 'Updated Product Name'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_menu_item_delete_success(self):
        """Test successful menu item deletion."""
        url = reverse('marketplace_menu_item_delete', kwargs={
            'write_uuid': self.store.write_uuid,
            'product_uuid': self.product.uuid
        })
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Menu item deleted successfully')
        
        # Verify product is deleted
        with self.assertRaises(StoreProductModel.DoesNotExist):
            StoreProductModel.objects.get(id=self.product.id)
    
    def test_menu_item_delete_invalid_write_uuid(self):
        """Test menu item deletion with invalid write_uuid."""
        invalid_write_uuid = uuid.uuid4()
        url = reverse('marketplace_menu_item_delete', kwargs={
            'write_uuid': invalid_write_uuid,
            'product_uuid': self.product.uuid
        })
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_menu_item_delete_invalid_product_uuid(self):
        """Test menu item deletion with invalid product_uuid."""
        invalid_product_uuid = uuid.uuid4()
        url = reverse('marketplace_menu_item_delete', kwargs={
            'write_uuid': self.store.write_uuid,
            'product_uuid': invalid_product_uuid
        })
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_menu_item_detail_success(self):
        """Test successful menu item detail retrieval."""
        url = reverse('marketplace_menu_item_detail', kwargs={
            'read_uuid': self.store.read_uuid,
            'product_uuid': self.product.uuid
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(self.product.uuid))
        self.assertEqual(response.data['name'], 'Test Product')
        self.assertEqual(response.data['description'], 'Test Product Description')
        self.assertEqual(Decimal(response.data['price']), Decimal('100.50'))
        self.assertEqual(response.data['store_name'], 'Test Store')
        self.assertEqual(response.data['store_currency'], 'руб.')

    def test_menu_item_detail_invalid_read_uuid(self):
        """Test menu item detail with invalid read_uuid."""
        invalid_read_uuid = uuid.uuid4()
        url = reverse('marketplace_menu_item_detail', kwargs={
            'read_uuid': invalid_read_uuid,
            'product_uuid': self.product.uuid
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Store not found')

    def test_menu_item_detail_invalid_product_uuid(self):
        """Test menu item detail with invalid product_uuid."""
        invalid_product_uuid = uuid.uuid4()
        url = reverse('marketplace_menu_item_detail', kwargs={
            'read_uuid': self.store.read_uuid,
            'product_uuid': invalid_product_uuid
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Menu item not found or does not belong to this store')

    def test_menu_item_detail_product_from_different_store(self):
        """Test menu item detail with product from a different store."""
        # Create another store with a product
        other_store = StoreModel.objects.create(
            name='Other Store',
            description='Other Description',
            currency='USD'
        )
        other_product = StoreProductModel.objects.create(
            store=other_store,
            name='Other Product',
            description='Other Product Description',
            price=Decimal('200.00')
        )

        # Try to access other_product using self.store's read_uuid
        url = reverse('marketplace_menu_item_detail', kwargs={
            'read_uuid': self.store.read_uuid,
            'product_uuid': other_product.uuid
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Menu item not found or does not belong to this store')


class CartAPITestCase(TestCase):
    """Test case for Cart API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )
        
        # Create multiple carts with different statuses and dates
        self.cart1 = CartModel.objects.create(
            store=self.store,
            status='created',
            date_created=datetime.now() - timedelta(days=5)
        )
        self.cart2 = CartModel.objects.create(
            store=self.store,
            status='sent',
            date_created=datetime.now() - timedelta(days=3)
        )
        self.cart3 = CartModel.objects.create(
            store=self.store,
            status='completed',
            date_created=datetime.now() - timedelta(days=1)
        )
        
        # Create a store for testing isolation
        self.other_store = StoreModel.objects.create(
            name='Other Store',
            description='Other Description',
            currency='USD'
        )
        self.other_cart = CartModel.objects.create(
            store=self.other_store,
            status='created'
        )
    
    def test_cart_list_success(self):
        """Test successful cart list retrieval."""
        url = reverse('marketplace_cart_list', kwargs={'write_uuid': self.store.write_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 3)  # Only carts for this store
        
        cart_uuids = [cart['uuid'] for cart in response.data['results']]
        self.assertIn(str(self.cart1.uuid), cart_uuids)
        self.assertIn(str(self.cart2.uuid), cart_uuids)
        self.assertIn(str(self.cart3.uuid), cart_uuids)
        self.assertNotIn(str(self.other_cart.uuid), cart_uuids)
    
    def test_cart_list_with_status_filter(self):
        """Test cart list with status filter."""
        url = reverse('marketplace_cart_list', kwargs={'write_uuid': self.store.write_uuid})
        response = self.client.get(url, {'status': 'sent'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['uuid'], str(self.cart2.uuid))
    
    def test_cart_list_with_date_filter(self):
        """Test cart list with date filter."""
        url = reverse('marketplace_cart_list', kwargs={'write_uuid': self.store.write_uuid})
        response = self.client.get(url, {
            'date_from': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),
            'date_to': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['uuid'], str(self.cart2.uuid))
    
    def test_cart_list_invalid_date_format(self):
        """Test cart list with invalid date format."""
        url = reverse('marketplace_cart_list', kwargs={'write_uuid': self.store.write_uuid})
        response = self.client.get(url, {'date_from': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Invalid date_from format', response.data['message'])
    
    def test_cart_list_invalid_write_uuid(self):
        """Test cart list with invalid write_uuid."""
        invalid_write_uuid = uuid.uuid4()
        url = reverse('marketplace_cart_list', kwargs={'write_uuid': invalid_write_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_cart_list_pagination(self):
        """Test cart list pagination."""
        # Create additional carts to test pagination
        for i in range(25):  # More than default page size
            CartModel.objects.create(
                store=self.store,
                status='created'
            )
        
        url = reverse('marketplace_cart_list', kwargs={'write_uuid': self.store.write_uuid})
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(response.data['count'], 28)  # 3 initial + 25 new
    
    def test_cart_status_update_success(self):
        """Test successful cart status update."""
        url = reverse('marketplace_cart_status_update', kwargs={'cart_uuid': self.cart1.uuid})
        data = {'status': 'sent'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart1.refresh_from_db()
        self.assertEqual(self.cart1.status, 'sent')
        self.assertEqual(response.data['status'], 'sent')
        self.assertEqual(response.data['status_display'], 'Sent')
    
    def test_cart_status_update_invalid_cart_uuid(self):
        """Test cart status update with invalid cart_uuid."""
        invalid_cart_uuid = uuid.uuid4()
        url = reverse('marketplace_cart_status_update', kwargs={'cart_uuid': invalid_cart_uuid})
        data = {'status': 'sent'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Cart not found')
    
    def test_cart_status_update_invalid_status(self):
        """Test cart status update with invalid status."""
        url = reverse('marketplace_cart_status_update', kwargs={'cart_uuid': self.cart1.uuid})
        data = {'status': 'invalid_status'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_cart_clear_items_success(self):
        """Test successful cart items clearing."""
        # Create a cart with items
        product1 = StoreProductModel.objects.create(
            store=self.store,
            name='Product 1',
            price=Decimal('50.00')
        )
        product2 = StoreProductModel.objects.create(
            store=self.store,
            name='Product 2',
            price=Decimal('75.00')
        )
        
        cart = CartModel.objects.create(store=self.store, status='created')
        CartItemModel.objects.create(cart=cart, menu_item=product1, quantity=2)
        CartItemModel.objects.create(cart=cart, menu_item=product2, quantity=1)
        
        # Verify cart has items before clearing
        self.assertEqual(cart.cart_items.count(), 2)
        self.assertEqual(cart.get_total_price(), Decimal('175.00'))
        
        url = reverse('marketplace_cart_clear_items', kwargs={'cart_uuid': cart.uuid})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(cart.uuid))
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(response.data['total_price'], '0.00')
        
        # Verify cart items are deleted from database
        self.assertEqual(cart.cart_items.count(), 0)
        self.assertEqual(cart.get_total_price(), Decimal('0'))
    
    def test_cart_clear_items_empty_cart(self):
        """Test clearing items from an already empty cart."""
        cart = CartModel.objects.create(store=self.store, status='created')
        
        # Verify cart is empty
        self.assertEqual(cart.cart_items.count(), 0)
        
        url = reverse('marketplace_cart_clear_items', kwargs={'cart_uuid': cart.uuid})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(response.data['total_price'], '0.00')
    
    def test_cart_clear_items_invalid_cart_uuid(self):
        """Test clearing items with invalid cart_uuid."""
        invalid_cart_uuid = uuid.uuid4()
        url = reverse('marketplace_cart_clear_items', kwargs={'cart_uuid': invalid_cart_uuid})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Cart not found')


class CheckoutOrderAPITestCase(TestCase):
    """Test case for Checkout Order API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.store = StoreModel.objects.create(
            name='Test Store',
            description='Test Description',
            currency='руб.'
        )
        self.product1 = StoreProductModel.objects.create(
            store=self.store,
            name='Test Product 1',
            description='Test Product Description 1',
            price=Decimal('100.00')
        )
        self.product2 = StoreProductModel.objects.create(
            store=self.store,
            name='Test Product 2',
            description='Test Product Description 2',
            price=Decimal('200.00')
        )
        self.cart = CartModel.objects.create(
            store=self.store,
            status='created'
        )
        CartItemModel.objects.create(
            cart=self.cart,
            menu_item=self.product1,
            quantity=2
        )
        CartItemModel.objects.create(
            cart=self.cart,
            menu_item=self.product2,
            quantity=1
        )

    def test_checkout_order_success_with_all_fields(self):
        """Test successful checkout with all buyer fields provided."""
        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': self.cart.uuid})
        data = {
            'buyer_name': 'Ivan Petrov',
            'buyer_phone': '+7 900 123-45-67',
            'buyer_address': 'Moscow, Red Square, 1'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'sent')
        self.assertEqual(response.data['status_display'], 'Sent')

        # Verify cart is updated in database
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, 'sent')
        self.assertEqual(self.cart.buyer_name, 'Ivan Petrov')
        self.assertEqual(self.cart.buyer_phone, '+7 900 123-45-67')
        self.assertEqual(self.cart.buyer_address, 'Moscow, Red Square, 1')

    def test_checkout_order_success_with_partial_fields(self):
        """Test successful checkout with only some buyer fields provided."""
        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': self.cart.uuid})
        data = {
            'buyer_name': 'Ivan Petrov',
            'buyer_phone': '+7 900 123-45-67'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'sent')

        # Verify cart is updated in database
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, 'sent')
        self.assertEqual(self.cart.buyer_name, 'Ivan Petrov')
        self.assertEqual(self.cart.buyer_phone, '+7 900 123-45-67')
        self.assertIsNone(self.cart.buyer_address)

    def test_checkout_order_success_without_buyer_fields(self):
        """Test successful checkout without any buyer fields (all optional)."""
        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': self.cart.uuid})
        data = {}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'sent')

        # Verify cart status is updated to 'sent'
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, 'sent')
        self.assertIsNone(self.cart.buyer_name)
        self.assertIsNone(self.cart.buyer_phone)
        self.assertIsNone(self.cart.buyer_address)

    def test_checkout_order_success_with_empty_strings(self):
        """Test successful checkout with empty string values."""
        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': self.cart.uuid})
        data = {
            'buyer_name': '',
            'buyer_phone': '',
            'buyer_address': ''
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'sent')

        # Verify cart is updated in database with None values (empty strings are converted)
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, 'sent')

    def test_checkout_order_cart_not_found(self):
        """Test checkout with invalid cart_uuid."""
        invalid_cart_uuid = uuid.uuid4()
        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': invalid_cart_uuid})
        data = {
            'buyer_name': 'Ivan Petrov'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Cart not found')

    def test_checkout_order_changes_status_to_sent(self):
        """Test that checkout always changes cart status to 'sent'."""
        # Create cart with different initial status
        cart = CartModel.objects.create(
            store=self.store,
            status='created'
        )
        CartItemModel.objects.create(
            cart=cart,
            menu_item=self.product1,
            quantity=1
        )

        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': cart.uuid})
        data = {'buyer_name': 'Test User'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart.refresh_from_db()
        self.assertEqual(cart.status, 'sent')

    def test_checkout_order_preserves_cart_items(self):
        """Test that checkout does not modify cart items."""
        initial_items_count = self.cart.cart_items.count()
        initial_total_price = self.cart.get_total_price()

        url = reverse('marketplace_checkout_order', kwargs={'cart_uuid': self.cart.uuid})
        data = {'buyer_name': 'Test User'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart.refresh_from_db()

        # Verify items are preserved
        self.assertEqual(self.cart.cart_items.count(), initial_items_count)
        self.assertEqual(self.cart.get_total_price(), initial_total_price)

        # Verify items in response
        self.assertEqual(len(response.data['items']), initial_items_count)
        self.assertEqual(Decimal(response.data['total_price']), initial_total_price)