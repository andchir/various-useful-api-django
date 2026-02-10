"""
Admin configuration for marketplace models.
"""
from django.contrib import admin
from marketplace.models import StoreModel, StoreProductModel, CartModel, CartItemModel


class MenuItemInline(admin.TabularInline):
    model = StoreProductModel
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


@admin.register(StoreProductModel)
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
