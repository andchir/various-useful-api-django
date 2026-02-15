"""
Marketplace views for stores, menu items, and shopping carts.
"""
import logging
from datetime import datetime
from rest_framework import permissions, status, pagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, inline_serializer

from marketplace.models import StoreModel, StoreProductModel, CartModel, CartItemModel
from marketplace.serializers import (
    StoreCreateSerializer, StoreResponseSerializer, StoreUpdateSerializer,
    StorePublicSerializer, StoreProductCreateSerializer, StoreProductUpdateSerializer,
    MenuItemResponseSerializer, CartResponseSerializer, AddToCartSerializer,
    RemoveFromCartSerializer, CartStatusUpdateSerializer, CheckoutSerializer,
    ErrorResponseSerializer
)

logger = logging.getLogger(__name__)


class CartPagination(PageNumberPagination):
    """Custom pagination for cart list."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(
    tags=['Store'],
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
            response_serializer = StoreResponseSerializer(store, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Store creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
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
            response_serializer = StoreResponseSerializer(store, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Store update error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=StoreProductCreateSerializer,
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

        serializer = StoreProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            menu_item = serializer.save(store=store)
            response_serializer = MenuItemResponseSerializer(menu_item, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Menu item creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
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

        store_serializer = StorePublicSerializer(store, context={'request': request})
        menu_items = StoreProductModel.objects.filter(store=store)
        menu_items_serializer = MenuItemResponseSerializer(menu_items, many=True, context={'request': request})

        return Response({
            'store': store_serializer.data,
            'menu_items': menu_items_serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Store menu list error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    responses={
        200: MenuItemResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def menu_item_detail(request, read_uuid, product_uuid):
    """
    Get single menu item details by product UUID using store's read_uuid.
    Returns menu item information.
    """
    try:
        try:
            store = StoreModel.objects.get(read_uuid=read_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found'},
                          status=status.HTTP_404_NOT_FOUND)

        try:
            menu_item = StoreProductModel.objects.get(uuid=product_uuid, store=store)
        except StoreProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Menu item not found or does not belong to this store'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = MenuItemResponseSerializer(menu_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Menu item detail error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=None,
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
        response_serializer = CartResponseSerializer(cart, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Cart creation error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
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
            menu_item = StoreProductModel.objects.get(uuid=menu_item_uuid, store=cart.store)
        except StoreProductModel.DoesNotExist:
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

        response_serializer = CartResponseSerializer(cart, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Cart add item error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
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
            menu_item = StoreProductModel.objects.get(uuid=menu_item_uuid)
        except StoreProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Menu item not found'},
                          status=status.HTTP_404_NOT_FOUND)

        try:
            cart_item = CartItemModel.objects.get(cart=cart, menu_item=menu_item)
            cart_item.delete()
        except CartItemModel.DoesNotExist:
            return Response({'success': False, 'message': 'Item not in cart'},
                          status=status.HTTP_404_NOT_FOUND)

        response_serializer = CartResponseSerializer(cart, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Cart remove item error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=None,
    responses={
        200: inline_serializer(
            name='StoreDeleteResponse',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
            }
        ),
        404: ErrorResponseSerializer,
    },
)
@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def store_delete(request, write_uuid):
    """
    Delete a store using write_uuid.
    Requires write_uuid for authorization.
    """
    try:
        try:
            store = StoreModel.objects.get(write_uuid=write_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found or invalid write_uuid'},
                          status=status.HTTP_404_NOT_FOUND)

        store.delete()
        return Response({'success': True, 'message': 'Store deleted successfully'},
                      status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Store deletion error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=StoreProductUpdateSerializer,
    responses={
        200: MenuItemResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def menu_item_update(request, write_uuid, product_uuid):
    """
    Update a menu item for a store.
    Requires store's write_uuid for authorization.
    """
    try:
        try:
            store = StoreModel.objects.get(write_uuid=write_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found or invalid write_uuid'},
                          status=status.HTTP_404_NOT_FOUND)

        try:
            menu_item = StoreProductModel.objects.get(uuid=product_uuid, store=store)
        except StoreProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Menu item not found or does not belong to this store'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = StoreProductUpdateSerializer(menu_item, data=request.data, partial=True)
        if serializer.is_valid():
            menu_item = serializer.save()
            response_serializer = MenuItemResponseSerializer(menu_item, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Menu item update error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=None,
    responses={
        200: inline_serializer(
            name='ProductDeleteResponse',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
            }
        ),
        404: ErrorResponseSerializer,
    },
)
@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def menu_item_delete(request, write_uuid, product_uuid):
    """
    Delete a menu item for a store.
    Requires store's write_uuid for authorization.
    """
    try:
        try:
            store = StoreModel.objects.get(write_uuid=write_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found or invalid write_uuid'},
                          status=status.HTTP_404_NOT_FOUND)

        try:
            menu_item = StoreProductModel.objects.get(uuid=product_uuid, store=store)
        except StoreProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Menu item not found or does not belong to this store'},
                          status=status.HTTP_404_NOT_FOUND)

        menu_item.delete()
        return Response({'success': True, 'message': 'Menu item deleted successfully'},
                      status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Menu item deletion error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=inline_serializer(
        name='CartListRequest',
        fields={
            'status': serializers.ChoiceField(choices=['created', 'sent', 'canceled', 'completed'], required=False),
            'date_from': serializers.DateField(required=False),
            'date_to': serializers.DateField(required=False),
        }
    ),
    responses={
        200: inline_serializer(
            name='CartListResponse',
            fields={
                'count': serializers.IntegerField(),
                'next': serializers.URLField(allow_null=True),
                'previous': serializers.URLField(allow_null=True),
                'results': CartResponseSerializer(many=True),
            }
        ),
        404: ErrorResponseSerializer,
    },
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cart_list(request, write_uuid):
    """
    Get list of carts for a store with filtering and pagination.
    Requires store's write_uuid for authorization.
    Filter by status, date_from, date_to (optional).
    """
    try:
        try:
            store = StoreModel.objects.get(write_uuid=write_uuid)
        except StoreModel.DoesNotExist:
            return Response({'success': False, 'message': 'Store not found or invalid write_uuid'},
                          status=status.HTTP_404_NOT_FOUND)

        carts = CartModel.objects.filter(store=store)

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            carts = carts.filter(status=status_filter)

        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                carts = carts.filter(date_created__date__gte=date_from_obj)
            except ValueError:
                return Response({'success': False, 'message': 'Invalid date_from format. Use YYYY-MM-DD'},
                              status=status.HTTP_400_BAD_REQUEST)

        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                carts = carts.filter(date_created__date__lte=date_to_obj)
            except ValueError:
                return Response({'success': False, 'message': 'Invalid date_to format. Use YYYY-MM-DD'},
                              status=status.HTTP_400_BAD_REQUEST)

        # Order by creation date descending
        carts = carts.order_by('-date_created')

        # Apply pagination
        paginator = CartPagination()
        paginated_carts = paginator.paginate_queryset(carts, request)
        serializer = CartResponseSerializer(paginated_carts, many=True, context={'request': request})

        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        logger.error(f"Cart list error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=CartStatusUpdateSerializer,
    responses={
        200: CartResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def cart_status_update(request, cart_uuid):
    """
    Update cart status by cart uuid.
    """
    try:
        try:
            cart = CartModel.objects.get(uuid=cart_uuid)
        except CartModel.DoesNotExist:
            return Response({'success': False, 'message': 'Cart not found'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = CartStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            cart.status = serializer.validated_data['status']
            cart.save()
            response_serializer = CartResponseSerializer(cart, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': serializer.errors},
                      status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Cart status update error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=None,
    responses={
        200: CartResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def cart_clear_items(request, cart_uuid):
    """
    Delete all items from cart by cart uuid.
    Returns empty cart with total price 0.
    """
    try:
        try:
            cart = CartModel.objects.get(uuid=cart_uuid)
        except CartModel.DoesNotExist:
            return Response({'success': False, 'message': 'Cart not found'},
                          status=status.HTTP_404_NOT_FOUND)

        # Delete all cart items
        deleted_count, _ = CartItemModel.objects.filter(cart=cart).delete()

        logger.info(f"Cart {cart_uuid} cleared: {deleted_count} items deleted")

        response_serializer = CartResponseSerializer(cart, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Cart clear items error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Store'],
    request=CheckoutSerializer,
    responses={
        200: CartResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def checkout_order(request, cart_uuid):
    """
    Checkout order by cart UUID.
    Updates cart with buyer information (optional fields) and sets status to 'sent'.
    Returns updated cart with buyer information.
    """
    try:
        try:
            cart = CartModel.objects.get(uuid=cart_uuid)
        except CartModel.DoesNotExist:
            return Response({'success': False, 'message': 'Cart not found'},
                          status=status.HTTP_404_NOT_FOUND)

        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'message': serializer.errors},
                          status=status.HTTP_400_BAD_REQUEST)

        # Update cart with buyer information
        cart.buyer_name = serializer.validated_data.get('buyer_name', None)
        cart.buyer_phone = serializer.validated_data.get('buyer_phone', None)
        cart.buyer_address = serializer.validated_data.get('buyer_address', None)
        cart.status = 'sent'
        cart.save()

        logger.info(f"Cart {cart_uuid} checked out with status 'sent'")

        response_serializer = CartResponseSerializer(cart, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Checkout order error: {str(e)}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
