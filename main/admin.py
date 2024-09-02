import os.path
from django.contrib import admin
from app import settings
from main.models import ProductModel, ImageModel, LogOwnerModel, LogItemModel


class ImagesInline(admin.TabularInline):
    model = ImageModel
    list_display = ('id', '__str__', 'image')
    fields = ('id', 'image')
    extra = 0
    can_delete = False
    show_change_link = True


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'price_currency', 'published', 'shop_name', 'shop_address', 'city')
    list_display_links = ('id', 'name')
    inlines = [ImagesInline]


@admin.register(ImageModel)
class ImageModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'product')
    list_display_links = ('id', 'image', 'product')

    def delete_file(self, obj):
        image_file_path = os.path.join(settings.MEDIA_ROOT, str(obj.image))
        if os.path.isfile(image_file_path):
            os.remove(image_file_path)

    def delete_model(self, request, obj):
        self.delete_file(obj)
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_file(obj)
        queryset.delete()


@admin.register(LogOwnerModel)
class ImageModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'uuid', 'date_created')
    list_display_links = ('id', 'name')


@admin.register(LogItemModel)
class LogItemModel(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'owner', 'date_created')
    list_display_links = ('id', 'uuid')
