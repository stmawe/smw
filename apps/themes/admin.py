"""Django admin for themes."""

from django.contrib import admin
from .models import Theme, ShopTheme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'is_built_in', 'is_active', 'created_at')
    list_filter = ('is_built_in', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'definition') if False else ()
    
    fieldsets = (
        ('Theme Information', {
            'fields': ('name', 'description', 'version', 'author')
        }),
        ('Settings', {
            'fields': ('is_built_in', 'is_active')
        }),
        ('Theme Definition', {
            'fields': ('definition',),
            'classes': ('collapse',),
        }),
        ('Preview', {
            'fields': ('preview_image',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of built-in themes
        if obj and obj.is_built_in:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ShopTheme)
class ShopThemeAdmin(admin.ModelAdmin):
    list_display = ('shop', 'theme', 'enabled', 'created_at')
    list_filter = ('enabled', 'theme')
    search_fields = ('shop__name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Shop & Theme', {
            'fields': ('shop', 'theme', 'enabled')
        }),
        ('Custom Overrides', {
            'fields': ('custom_overrides',),
            'description': 'Override theme properties in JSON format'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
