from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # For customizing User admin
from .models import Client, ClientDomain, User, Category

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'type', 'on_trial', 'paid_until') # Add created_on if you add it to model
    search_fields = ('name', 'schema_name')
    list_filter = ('type', 'on_trial')

@admin.register(ClientDomain)
class ClientDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    search_fields = ('domain', 'tenant__name')
    list_filter = ('is_primary', 'tenant__type')

# Customize the User admin
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}), # Add your custom 'role' field here
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = BaseUserAdmin.list_display + ('role',)
    list_filter = BaseUserAdmin.list_filter + ('role',)


admin.site.register(User, UserAdmin) # Register User with the custom admin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    # If you add slug:
    # prepopulated_fields = {'slug': ('name',)}