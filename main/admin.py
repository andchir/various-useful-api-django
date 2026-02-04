import os.path
from django.contrib import admin
from app import settings
from main.models import ProductModel, ImageModel, LogOwnerModel, LogItemModel, StoreModel, MenuItemModel, CartModel, CartItemModel


class LogsInline(admin.TabularInline):
    model = LogItemModel
    fields = ('id', 'date_created', 'name', 'data')
    readonly_fields = ('date_created', 'name', 'data')
    ordering = ('-id',)
    extra = 0
    can_delete = False
    show_change_link = True


class ImagesInline(admin.TabularInline):
    model = ImageModel
    list_display = ('id', '__str__', 'image')
    fields = ('id', 'image')
    max_num = 100
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
class LogOwnerModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'uuid', 'date_created')
    list_display_links = ('id', 'name')
    inlines = [LogsInline]


@admin.register(LogItemModel)
class LogItemModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'owner', 'date_created')
    list_display_links = ('id', 'uuid')


class MenuItemInline(admin.TabularInline):
    model = MenuItemModel
    fields = ('id', 'name', 'price', 'uuid', 'date_created')
    readonly_fields = ('id', 'uuid', 'date_created')
    ordering = ('-id',)
    extra = 0
    can_delete = True
    show_change_link = True


class CartItemInline(admin.TabularInline):
    model = CartItemModel
    fields = ('id', 'menu_item', 'quantity', 'date_created')
    readonly_fields = ('date_created',)
    ordering = ('-id',)
    extra = 0
    can_delete = True
    show_change_link = True


@admin.register(StoreModel)
class StoreModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'currency', 'read_uuid', 'write_uuid', 'date_created')
    list_display_links = ('id', 'name')
    readonly_fields = ('read_uuid', 'write_uuid', 'date_created', 'date_updated')
    inlines = [MenuItemInline]
    search_fields = ('name', 'read_uuid', 'write_uuid')


@admin.register(MenuItemModel)
class MenuItemModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'store', 'uuid', 'date_created')
    list_display_links = ('id', 'name')
    readonly_fields = ('uuid', 'date_created', 'date_updated')
    search_fields = ('name', 'uuid')
    list_filter = ('store',)


@admin.register(CartModel)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'store', 'date_created', 'get_total_price')
    list_display_links = ('id', 'uuid')
    readonly_fields = ('uuid', 'date_created', 'date_updated')
    inlines = [CartItemInline]
    search_fields = ('uuid',)
    list_filter = ('store',)


@admin.register(CartItemModel)
class CartItemModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'menu_item', 'quantity', 'get_total_price', 'date_created')
    list_display_links = ('id',)
    readonly_fields = ('date_created', 'date_updated')
    search_fields = ('cart__uuid', 'menu_item__name')
    list_filter = ('cart__store',)
