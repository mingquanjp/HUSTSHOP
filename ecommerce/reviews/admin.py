from django.contrib import admin
from reviews.models import Review



class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating','review', 'status', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')

admin.site.register(Review, ReviewAdmin)

