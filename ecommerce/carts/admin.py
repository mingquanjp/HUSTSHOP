from django.contrib import admin
from .models import Cart, CartItem


class CartAdmin(admin.ModelAdmin):
    llist_display = ('cart_id', 'user', 'date_added',)
    list_filter = ('date_added', 'user')
    search_fields = ('cart_id', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('date_added',)


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_cart_info', 'quantity', 'is_active', 'sub_total')
    list_filter = ('is_active', 'cart__user')
    search_fields = ('product__product_name', 'cart__user__email')

    def get_cart_info(self, obj):
        if obj.cart:
            if obj.cart.user:
                return f"Cart của {obj.cart.user.email}"
            else:
                return f"Cart: {obj.cart.cart_id[:20]}..."
        return "No Cart"
    get_cart_info.short_description = 'Cart Info'

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)