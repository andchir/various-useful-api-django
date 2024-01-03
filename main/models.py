from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django_advance_thumbnail import AdvanceThumbnailField
from django_resized import ResizedImageField


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
