from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class ProductModel(models.Model):
    CURRENCIES_CHOICES = (
        ('RUB', 'Руб.'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    )

    id = models.BigAutoField(primary_key=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(auto_now_add=False)
    user = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    published = models.BooleanField(default=False)
    price = models.FloatField()
    price_currency = models.CharField(max_length=10, choices=CURRENCIES_CHOICES)
    shop_name = models.CharField(max_length=200)
    shop_address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product-detail', args=[str(self.id)])


class ImageModel(models.Model):
    product = models.ForeignKey(ProductModel, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='media/%Y/%m/%d/', blank=True)

    class Meta:
        db_table = 'images'

    def __str__(self):
        return "%s" % (self.product.name)
