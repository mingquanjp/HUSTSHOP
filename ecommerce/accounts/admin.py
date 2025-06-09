from django.contrib import admin
from .models import Account  # Assuming your model name is Account


class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'date_joined', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'role', 'date_joined')
    list_editable = ('is_active',)
    ordering = ('-date_joined',)

admin.site.register(Account, AccountAdmin)
