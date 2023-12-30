from django.contrib import admin
from main.models import ProductModel


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'price_currency', 'published', 'shop_name', 'shop_address', 'city')
    list_display_links = ('id', 'name')
    # exclude = ('bodyFields', 'headers', 'responseHeaders')
