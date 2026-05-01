from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # For customizing User admin
from .models import Client, ClientDomain, User, Category
from .models import ThemeToken, Theme, PageThemeAssignment, ThemeComponentLibrary, ThemeChangeLog

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'tenant_type', 'on_trial', 'paid_until')
    search_fields = ('name', 'schema_name')
    list_filter = ('tenant_type', 'on_trial')

@admin.register(ClientDomain)
class ClientDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    search_fields = ('domain', 'tenant__name')
    list_filter = ('is_primary', 'tenant__tenant_type')

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


# ============================================================
# THEME SYSTEM ADMIN
# ============================================================

@admin.register(ThemeToken)
class ThemeTokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'css_custom_property', 'default_value', 'is_global')
    list_filter = ('category', 'is_global')
    search_fields = ('name', 'css_custom_property', 'description')
    ordering = ['category', 'name']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Token Identity', {
            'fields': ('name', 'category', 'css_custom_property')
        }),
        ('Value', {
            'fields': ('default_value',)
        }),
        ('Metadata', {
            'fields': ('description', 'is_global', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'theme_type', 'is_active', 'is_public', 'created_by', 'created_at')
    list_filter = ('theme_type', 'is_active', 'is_public', 'created_at')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ['-is_active', '-created_at']
    
    fieldsets = (
        ('Theme Identity', {
            'fields': ('name', 'slug', 'description', 'theme_type')
        }),
        ('Customization', {
            'fields': ('token_overrides', 'custom_css'),
            'description': 'Override design tokens and add custom CSS for this theme'
        }),
        ('Status', {
            'fields': ('is_active', 'is_public', 'created_by'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PageThemeAssignment)
class PageThemeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('page_type', 'theme', 'override_enabled', 'created_at')
    list_filter = ('page_type', 'override_enabled')
    search_fields = ('page_type', 'page_route', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Page Configuration', {
            'fields': ('page_type', 'page_route')
        }),
        ('Theme Assignment', {
            'fields': ('theme', 'override_enabled')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ThemeComponentLibrary)
class ThemeComponentLibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'version', 'is_draft', 'is_published', 'created_by', 'created_at')
    list_filter = ('is_draft', 'is_published', 'created_at')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ['-is_published', 'name', '-version']
    
    fieldsets = (
        ('Component Identity', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Template Code', {
            'fields': ('html_template', 'inline_css', 'inline_js'),
            'description': 'HTML, CSS, and JavaScript for this component'
        }),
        ('Versioning', {
            'fields': ('version', 'is_draft', 'is_published', 'theme'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ThemeChangeLog)
class ThemeChangeLogAdmin(admin.ModelAdmin):
    list_display = ('theme', 'change_type', 'changed_field', 'changed_by', 'created_at')
    list_filter = ('change_type', 'theme', 'created_at')
    search_fields = ('theme__name', 'reason', 'changed_field')
    readonly_fields = ('created_at', 'theme', 'change_type', 'changed_field', 'old_value', 'new_value', 'changed_by')
    
    def has_add_permission(self, request):
        return False  # Change log is read-only