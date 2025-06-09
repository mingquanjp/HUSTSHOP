from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Product, Variation, Category


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'created_at', 'updated_at', 'is_available')
    prepopulated_fields = {'slug': ('name',)}


class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'manager', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}



admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(Category, CategoryAdmin)

# Register your models here.
