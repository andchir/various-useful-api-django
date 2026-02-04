"""
Marketplace views for stores, menu items, and shopping carts.
"""
import logging
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from main.marketplace.models import StoreModel, MenuItemModel, CartModel, CartItemModel
from main.marketplace.serializers import (
    StoreCreateSerializer, StoreResponseSerializer, StoreUpdateSerializer,
    StorePublicSerializer, MenuItemCreateSerializer, MenuItemResponseSerializer,
    CartResponseSerializer, AddToCartSerializer, RemoveFromCartSerializer, ErrorResponseSerializer
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Marketplace'],
    request=StoreCreateSerializer,
    responses={
        201: StoreResponseSerializer,
        400: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def store_create(request):
    """
    Create a new store.
    Returns store data including read_uuid and write_uuid.
    """
    try:
        serializer = StoreCreateSerializer(data=request.data)
        if serializer.is_valid():
            store = serializer.save()
            response_serializer = StoreResponseSerializer(store)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Store creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Marketplace'],
    request=StoreUpdateSerializer,
    responses={
        200: StoreResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def store_update(request, write_uuid):
    """
    Update store details using write_uuid.
    Requires write_uuid for authorization.
    """
    try:
        try:
            store = StoreModel.objects.get(write_uuid=write_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found or invalid write_uuid'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = StoreUpdateSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            store = serializer.save()
            response_serializer = StoreResponseSerializer(store)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Store update error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Marketplace'],
    request=MenuItemCreateSerializer,
    responses={
        201: MenuItemResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def menu_item_create(request, write_uuid):
    """
    Create a new menu item for a store.
    Requires store's write_uuid for authorization.
    """
    try:
        try:
            store = StoreModel.objects.get(write_uuid=write_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found or invalid write_uuid'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = MenuItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            menu_item = serializer.save(store=store)
            response_serializer = MenuItemResponseSerializer(menu_item)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Menu item creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Marketplace'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'store': StorePublicSerializer,
                'menu_items': {'type': 'array', 'items': MenuItemResponseSerializer}
            }
        },
        404: ErrorResponseSerializer,
    },
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def store_menu_list(request, read_uuid):
    """
    Get store details and menu items list by read_uuid.
    Returns store info (excluding write_uuid) and all menu items.
    """
    try:
        try:
            store = StoreModel.objects.get(read_uuid=read_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found'},
                          status=status.HTTP_404_NOT_FOUND)

        store_serializer = StorePublicSerializer(store)
        menu_items = MenuItemModel.objects.filter(store=store)
        menu_items_serializer = MenuItemResponseSerializer(menu_items, many=True)

        return Response({
            'store': store_serializer.data,
            'menu_items': menu_items_serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Store menu list error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Marketplace'],
    responses={
        201: CartResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cart_create(request, read_uuid):
    """
    Create a new cart for a store.
    Requires store's read_uuid.
    Returns cart with UUID.
    """
    try:
        try:
            store = StoreModel.objects.get(read_uuid=read_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found'},
                          status=status.HTTP_404_NOT_FOUND)

        cart = CartModel.objects.create(store=store)
        response_serializer = CartResponseSerializer(cart)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Cart creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Marketplace'],
    request=AddToCartSerializer,
    responses={
        200: CartResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cart_add_item(request, cart_uuid):
    """
    Add a menu item to cart or update quantity if already exists.
    Returns full cart contents with total price.
    """
    try:
        try:
            cart = CartModel.objects.get(uuid=cart_uuid)
        except CartModel.DoesNotExist:
            return Response({'success': False, 'message': 'Cart not found'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'message': serializer.errors},
                          status=status.HTTP_400_BAD_REQUEST)

        menu_item_uuid = serializer.validated_data['menu_item_uuid']
        quantity = serializer.validated_data['quantity']

        try:
            menu_item = MenuItemModel.objects.get(uuid=menu_item_uuid, store=cart.store)
        except MenuItemModel.DoesNotExist:
            return Response({'success': False, 'message': 'Menu item not found or does not belong to this store'},
                          status=status.HTTP_404_NOT_FOUND)

        # Check if item already in cart, update quantity or create new
        cart_item, created = CartItemModel.objects.get_or_create(
            cart=cart,
            menu_item=menu_item,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity = quantity
            cart_item.save()

        response_serializer = CartResponseSerializer(cart)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Cart add item error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Marketplace'],
    request=RemoveFromCartSerializer,
    responses={
        200: CartResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cart_remove_item(request, cart_uuid):
    """
    Remove a menu item from cart.
    Returns full cart contents with total price.
    """
    try:
        try:
            cart = CartModel.objects.get(uuid=cart_uuid)
        except CartModel.DoesNotExist:
            return Response({'success': False, 'message': 'Cart not found'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = RemoveFromCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'message': serializer.errors},
                          status=status.HTTP_400_BAD_REQUEST)

        menu_item_uuid = serializer.validated_data['menu_item_uuid']

        try:
            menu_item = MenuItemModel.objects.get(uuid=menu_item_uuid)
        except MenuItemModel.DoesNotExist:
            return Response({'success': False, 'message': 'Menu item not found'},
                          status=status.HTTP_404_NOT_FOUND)

        try:
            cart_item = CartItemModel.objects.get(cart=cart, menu_item=menu_item)
            cart_item.delete()
        except CartItemModel.DoesNotExist:
            return Response({'success': False, 'message': 'Item not in cart'},
                          status=status.HTTP_404_NOT_FOUND)

        response_serializer = CartResponseSerializer(cart)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Cart remove item error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
