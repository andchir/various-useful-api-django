from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django_advance_thumbnail import AdvanceThumbnailField
from django_resized import ResizedImageField
import uuid

from app.settings import ADMIN_LOG_OWNER_SECTION_NAME


class ProductModel(models.Model):
    CURRENCIES_CHOICES = (
        ('RUB', 'Руб.'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    )
    UNIT_CHOICES = (
        ('piece', '1 штука'),
        ('kg', '1 кг')
    )

    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(auto_now_add=False)
    user = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    published = models.BooleanField(default=False)
    price = models.FloatField()
    price_currency = models.CharField(max_length=10, choices=CURRENCIES_CHOICES, default='RUB')
    price_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='piece')
    shop_name = models.CharField(max_length=200)
    shop_address = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product-detail', args=[str(self.id)])


class ImageModel(models.Model):
    product = models.ForeignKey(ProductModel, related_name='images', on_delete=models.CASCADE)
    # image = models.ImageField(upload_to='images/%Y/%m/%d/', blank=True)
    image = ResizedImageField(size=[1920, 1080], scale=1, upload_to='images/%Y/%m/%d/', blank=True)
    thumbnail = AdvanceThumbnailField(source_field='image', upload_to='thumbnails/%Y/%m/%d/', null=True, blank=True,
                                      size=(400, 400))

    class Meta:
        db_table = 'images'
        verbose_name = 'Photo'

    def __str__(self):
        return "%s" % (self.product.name)


class LogOwnerModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='log_owner', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    site_url = models.CharField(max_length=200, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid1, editable=False)
    data = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'log_owners'
        verbose_name = ADMIN_LOG_OWNER_SECTION_NAME
        verbose_name_plural = ADMIN_LOG_OWNER_SECTION_NAME

    def __str__(self):
        return "%s-%s" % (self.name, self.uuid)


class LogItemModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(LogOwnerModel, related_name='log_items', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid1, editable=True, blank=True, null=True)

    class Meta:
        db_table = 'log'
        verbose_name = 'Log'

    def __str__(self):
        return "%s-%s" % (self.owner.name, self.id)


class StoreModel(models.Model):
    """
    Модель торговой точки (Store/Point of Sale)
    """
    CURRENCY_CHOICES = (
        ('руб.', 'Рубли'),
        ('EUR', 'Евро'),
        ('USD', 'Доллары'),
    )

    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=200, verbose_name='Название торговой точки')
    description = models.TextField(blank=True, null=True, verbose_name='Дополнительная информация')
    logo = ResizedImageField(
        size=[800, 800],
        scale=1,
        upload_to='stores/logos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Логотип'
    )
    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='руб.',
        verbose_name='Валюта'
    )
    read_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Read UUID')
    write_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Write UUID')

    class Meta:
        db_table = 'stores'
        verbose_name = 'Торговая точка'
        verbose_name_plural = 'Торговые точки'

    def __str__(self):
        return self.name


class MenuItemModel(models.Model):
    """
    Модель товара в меню (каталоге)
    """
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(StoreModel, related_name='menu_items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, verbose_name='Название товара')
    description = models.TextField(blank=True, null=True, verbose_name='Описание товара')
    photo = ResizedImageField(
        size=[1920, 1080],
        scale=1,
        upload_to='stores/menu_items/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Фото товара'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = 'menu_items'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class CartModel(models.Model):
    """
    Модель корзины заказа
    """
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(StoreModel, related_name='carts', on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f"Cart {self.uuid} - {self.store.name}"

    def get_total_price(self):
        """Вычисляет общую стоимость корзины"""
        total = sum(item.get_total_price() for item in self.cart_items.all())
        return total


class CartItemModel(models.Model):
    """
    Модель товара в корзине
    """
    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    cart = models.ForeignKey(CartModel, related_name='cart_items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItemModel, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = ('cart', 'menu_item')  # Один товар может быть только один раз в корзине

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

    def get_total_price(self):
        """Вычисляет стоимость позиции"""
        return self.menu_item.price * self.quantity
