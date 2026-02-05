"""
Marketplace models for stores, menu items, and shopping carts.
"""
from decimal import Decimal
from django.db import models
from django_resized import ResizedImageField
import uuid


class StoreModel(models.Model):
    """
    Store/Point of Sale model.
    """
    CURRENCY_CHOICES = (
        ('руб.', 'Rubles'),
        ('EUR', 'Euro'),
        ('USD', 'Dollars'),
    )

    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=200, verbose_name='Store name')
    description = models.TextField(blank=True, null=True, verbose_name='Additional information')
    logo = ResizedImageField(
        size=[800, 800],
        scale=1,
        upload_to='stores/logos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Logo'
    )
    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='руб.',
        verbose_name='Currency'
    )
    read_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Read UUID')
    write_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Write UUID')

    class Meta:
        db_table = 'stores'
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'

    def __str__(self):
        return self.name


class MenuItemModel(models.Model):
    """
    Menu item (product catalog) model.
    """
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(StoreModel, related_name='menu_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name='Product name')
    description = models.TextField(blank=True, null=True, verbose_name='Product description')
    photo = ResizedImageField(
        size=[1920, 1080],
        scale=1,
        upload_to='stores/menu_items/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Product photo'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = 'menu_items'
        verbose_name = 'Menu item'
        verbose_name_plural = 'Menu items'

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class CartModel(models.Model):
    """
    Shopping cart model.
    """
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(StoreModel, related_name='carts', on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart {self.uuid} - {self.store.name}"

    def get_total_price(self) -> Decimal:
        """Calculate total cart price."""
        total = sum(item.get_total_price() for item in self.cart_items.all())
        return Decimal(str(total))


class CartItemModel(models.Model):
    """
    Cart item model.
    """
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    cart = models.ForeignKey(CartModel, related_name='cart_items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItemModel, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Cart item'
        verbose_name_plural = 'Cart items'
        unique_together = ('cart', 'menu_item')  # One item can only appear once in a cart

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

    def get_total_price(self) -> Decimal:
        """Calculate line item total price."""
        return self.menu_item.price * self.quantity
