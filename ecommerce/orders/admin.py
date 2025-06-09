from django.contrib import admin
from .models import Payment, Order, OrderProduct, Promotion, UserHavePromotion


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ('product', 'quantity', 'product_price', 'subtotal')
    can_delete = False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user', 'payment_method', 'amount_paid', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('payment_id', 'user__email')
    readonly_fields = ('created_at', )

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('discount_code', 'name', 'discount_value', 'quantity', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'discount_code')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserHavePromotion)
class UserHavePromotionAdmin(admin.ModelAdmin):
    list_display = ('user', 'promotion', 'used_at', 'order')
    search_fields = ('user__email', 'promotion__discount_code')
    autocomplete_fields = ['user', 'promotion', 'order']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'order_status', 'order_total', 'created_at')
    list_filter = ('order_status', 'created_at')
    search_fields = ('order_number', 'user__email')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderProductInline]
    actions = ['mark_as_processing', 'mark_as_completed']

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} orders have been marked as processing')

    mark_as_processing.short_description = "Mark as Processing"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} orders have been marked as completed')
    mark_as_completed.short_description = "Mark as Complete"

@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'subtotal')
    list_filter = ('order__order_status',)
    search_fields = ('order__order_number', 'product__name')