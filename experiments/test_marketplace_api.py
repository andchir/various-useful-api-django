"""
Experiment script for manually testing Marketplace API

This script demonstrates how to use the Marketplace API endpoints.
Run this after the server is started to test the full workflow.

Usage:
    python experiments/test_marketplace_api.py
"""

import requests
import json
import uuid

# Base URL - adjust if needed
BASE_URL = "http://localhost:8000/api/v1"


def print_response(title, response):
    """Helper to print formatted response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")


def test_marketplace_workflow():
    """Test the complete marketplace workflow"""

    print("Starting Marketplace API Test Workflow...")

    # 1. Create a store
    print("\n1. Creating a store...")
    store_data = {
        "name": "Кофейня 'Утро'",
        "description": "Уютная кофейня в центре города",
        "currency": "руб."
    }
    response = requests.post(f"{BASE_URL}/store/create", json=store_data)
    print_response("CREATE STORE", response)

    if response.status_code != 201:
        print("Failed to create store. Exiting.")
        return

    store_response = response.json()
    read_uuid = store_response['read_uuid']
    write_uuid = store_response['write_uuid']

    print(f"Store created successfully!")
    print(f"Read UUID: {read_uuid}")
    print(f"Write UUID: {write_uuid}")

    # 2. Update the store
    print("\n2. Updating the store...")
    update_data = {
        "description": "Уютная кофейня в центре города. Работаем с 8:00 до 22:00"
    }
    response = requests.put(f"{BASE_URL}/store/update/{write_uuid}", json=update_data)
    print_response("UPDATE STORE", response)

    # 3. Create menu items
    print("\n3. Creating menu items...")

    menu_items = [
        {
            "name": "Американо",
            "description": "Классический кофе американо",
            "price": "150.00"
        },
        {
            "name": "Капучино",
            "description": "Кофе с молочной пенкой",
            "price": "180.00"
        },
        {
            "name": "Круассан",
            "description": "Свежий французский круассан",
            "price": "120.00"
        },
        {
            "name": "Чизкейк",
            "description": "Домашний чизкейк",
            "price": "250.00"
        }
    ]

    created_items = []
    for item in menu_items:
        response = requests.post(f"{BASE_URL}/store/{write_uuid}/menu/create", json=item)
        print_response(f"CREATE MENU ITEM: {item['name']}", response)
        if response.status_code == 201:
            created_items.append(response.json())

    # 4. Get store menu list
    print("\n4. Getting store menu list...")
    response = requests.get(f"{BASE_URL}/store/{read_uuid}/menu")
    print_response("GET STORE MENU", response)

    # 5. Create a cart
    print("\n5. Creating a cart...")
    response = requests.post(f"{BASE_URL}/cart/create/{read_uuid}")
    print_response("CREATE CART", response)

    if response.status_code != 201:
        print("Failed to create cart. Exiting.")
        return

    cart_response = response.json()
    cart_uuid = cart_response['uuid']
    print(f"Cart created successfully! UUID: {cart_uuid}")

    # 6. Add items to cart
    print("\n6. Adding items to cart...")

    if len(created_items) >= 2:
        # Add 2 Американо
        add_data = {
            "menu_item_uuid": created_items[0]['uuid'],
            "quantity": 2
        }
        response = requests.post(f"{BASE_URL}/cart/{cart_uuid}/add", json=add_data)
        print_response("ADD TO CART: 2x Американо", response)

        # Add 1 Капучино
        add_data = {
            "menu_item_uuid": created_items[1]['uuid'],
            "quantity": 1
        }
        response = requests.post(f"{BASE_URL}/cart/{cart_uuid}/add", json=add_data)
        print_response("ADD TO CART: 1x Капучино", response)

        # Add 1 Круассан
        if len(created_items) >= 3:
            add_data = {
                "menu_item_uuid": created_items[2]['uuid'],
                "quantity": 1
            }
            response = requests.post(f"{BASE_URL}/cart/{cart_uuid}/add", json=add_data)
            print_response("ADD TO CART: 1x Круассан", response)

        # 7. Update quantity in cart (change Американо from 2 to 3)
        print("\n7. Updating item quantity in cart...")
        add_data = {
            "menu_item_uuid": created_items[0]['uuid'],
            "quantity": 3
        }
        response = requests.post(f"{BASE_URL}/cart/{cart_uuid}/add", json=add_data)
        print_response("UPDATE CART: 3x Американо", response)

        # 8. Remove item from cart
        print("\n8. Removing item from cart...")
        remove_data = {
            "menu_item_uuid": created_items[2]['uuid']
        }
        response = requests.post(f"{BASE_URL}/cart/{cart_uuid}/remove", json=remove_data)
        print_response("REMOVE FROM CART: Круассан", response)

    # 9. Test error cases
    print("\n9. Testing error cases...")

    # Try to update store with invalid write_uuid
    print("\n9a. Try to update store with invalid write_uuid...")
    invalid_uuid = str(uuid.uuid4())
    response = requests.put(f"{BASE_URL}/store/update/{invalid_uuid}", json={"name": "Test"})
    print_response("UPDATE WITH INVALID UUID (should fail)", response)

    # Try to add item from non-existent menu item
    print("\n9b. Try to add non-existent item to cart...")
    invalid_uuid = str(uuid.uuid4())
    add_data = {
        "menu_item_uuid": invalid_uuid,
        "quantity": 1
    }
    response = requests.post(f"{BASE_URL}/cart/{cart_uuid}/add", json=add_data)
    print_response("ADD INVALID ITEM (should fail)", response)

    print("\n" + "="*60)
    print("Marketplace API Test Workflow Completed!")
    print("="*60)


if __name__ == "__main__":
    try:
        test_marketplace_workflow()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print(f"Please make sure the server is running at {BASE_URL}")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
