"""
Marketplace serializers for stores, menu items, and shopping carts.
"""
from decimal import Decimal
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from marketplace.models import StoreModel, MenuItemModel, CartModel, CartItemModel


class StoreCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new store."""
    logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = StoreModel
        fields = ('name', 'description', 'logo', 'currency')

    def validate_logo(self, value):
        """Validate logo file size (max 5MB) and type."""
        if value:
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("File size must not exceed 5 MB")

            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("Allowed formats: JPEG, PNG, GIF, WEBP")

        return value


class StoreResponseSerializer(serializers.ModelSerializer):
    """Serializer for store response with read and write UUIDs."""
    logo = serializers.SerializerMethodField()

    class Meta:
        model = StoreModel
        fields = ('id', 'date_created', 'date_updated', 'name', 'description', 'logo', 'currency', 'read_uuid', 'write_uuid')
        read_only_fields = ('id', 'date_created', 'date_updated', 'read_uuid', 'write_uuid')

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_logo(self, obj):
        """Return full URL for logo image."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class StorePublicSerializer(serializers.ModelSerializer):
    """Serializer for public store view (excludes write_uuid)."""
    logo = serializers.SerializerMethodField()

    class Meta:
        model = StoreModel
        fields = ('id', 'name', 'description', 'logo', 'currency', 'read_uuid')
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_logo(self, obj):
        """Return full URL for logo image."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class StoreUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating store."""
    logo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = StoreModel
        fields = ('name', 'description', 'logo', 'currency')

    def validate_logo(self, value):
        """Validate logo file size (max 5MB) and type."""
        if value:
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("File size must not exceed 5 MB")

            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("Allowed formats: JPEG, PNG, GIF, WEBP")

        return value


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a menu item."""
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = MenuItemModel
        fields = ('name', 'description', 'photo', 'price')

    def validate_photo(self, value):
        """Validate photo file size (max 5MB) and type."""
        if value:
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("File size must not exceed 5 MB")

            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("Allowed formats: JPEG, PNG, GIF, WEBP")

        return value


class MenuItemResponseSerializer(serializers.ModelSerializer):
    """Serializer for menu item response."""
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_currency = serializers.CharField(source='store.currency', read_only=True)
    photo = serializers.SerializerMethodField()

    class Meta:
        model = MenuItemModel
        fields = ('id', 'uuid', 'date_created', 'date_updated', 'name', 'description', 'photo', 'price', 'store_name', 'store_currency')
        read_only_fields = ('id', 'uuid', 'date_created', 'date_updated', 'store_name', 'store_currency')

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo(self, obj):
        """Return full URL for photo image."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart item with price calculation."""
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(source='menu_item.price', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.SerializerMethodField()
    menu_item_uuid = serializers.UUIDField(source='menu_item.uuid', read_only=True)

    class Meta:
        model = CartItemModel
        fields = ('id', 'menu_item_uuid', 'menu_item_name', 'menu_item_price', 'quantity', 'total_price')
        read_only_fields = ('id', 'menu_item_name', 'menu_item_price', 'total_price', 'menu_item_uuid')

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_price(self, obj) -> Decimal:
        return obj.get_total_price()


class CartResponseSerializer(serializers.ModelSerializer):
    """Serializer for cart response with items and total."""
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_currency = serializers.CharField(source='store.currency', read_only=True)

    class Meta:
        model = CartModel
        fields = ('uuid', 'store_name', 'store_currency', 'date_created', 'date_updated', 'items', 'total_price')
        read_only_fields = fields

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_price(self, obj) -> Decimal:
        return obj.get_total_price()


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding item to cart."""
    menu_item_uuid = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)


class RemoveFromCartSerializer(serializers.Serializer):
    """Serializer for removing item from cart."""
    menu_item_uuid = serializers.UUIDField(required=True)


class ErrorResponseSerializer(serializers.Serializer):
    """Generic error response serializer."""
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
