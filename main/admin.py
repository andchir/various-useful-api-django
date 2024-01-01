import os.path
from django.contrib import admin
from app import settings
from main.models import ProductModel, ImageModel


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'price_currency', 'published', 'shop_name', 'shop_address', 'city')
    list_display_links = ('id', 'name')


@admin.register(ImageModel)
class ImageModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'product')
    list_display_links = ('id', 'image', 'product')

    def delete_model(self, request, obj):
        image_file_path = os.path.join(settings.MEDIA_ROOT, str(obj.image))
        if os.path.isfile(image_file_path):
            os.remove(image_file_path)
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            image_file_path = os.path.join(settings.MEDIA_ROOT, str(obj.image))
            if os.path.isfile(image_file_path):
                os.remove(image_file_path)
        queryset.delete()
