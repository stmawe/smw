"""Theme Engine - Core theme processing and rendering."""

from django.core.cache import cache
from .models import Theme, ShopTheme


class ThemeEngine:
    """
    Main theme engine for UniMarket.
    Handles theme loading, parsing, compilation, and injection.
    """
    
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(self, shop=None):
        """Initialize theme engine for a shop."""
        self.shop = shop
        self.theme = None
        self.shop_theme = None
        
        if shop:
            self._load_shop_theme()
    
    def _load_shop_theme(self):
        """Load shop's theme configuration."""
        try:
            self.shop_theme = ShopTheme.objects.select_related('theme').get(
                shop=self.shop
            )
            if self.shop_theme.enabled:
                self.theme = self.shop_theme.theme
            else:
                self.theme = self._get_default_theme()
                self.shop_theme = None
        except ShopTheme.DoesNotExist:
            # Use default theme if not configured
            self.theme = self._get_default_theme()
            self.shop_theme = None
    
    @staticmethod
    def _get_default_theme():
        """Get default theme (usually 'light')."""
        try:
            return Theme.objects.get(name='light', is_built_in=True)
        except Theme.DoesNotExist:
            return None
    
    def get_css(self):
        """
        Get compiled CSS with all custom properties.
        Cached for performance.
        """
        cache_key = f'theme_css_shop_{self.shop.id}' if self.shop else 'theme_css_default'
        
        # Try to get from cache
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        css = ""
        
        if self.shop_theme:
            css = self.shop_theme.get_css_string()
        elif self.theme:
            properties = self.theme.get_all_properties()
            css = self._properties_to_css(properties)
        
        # Cache the result
        cache.set(cache_key, css, self.CACHE_TTL)
        return css
    
    @staticmethod
    def _properties_to_css(properties):
        """Convert property dict to CSS rule."""
        if not properties:
            return ""
        
        lines = [":root {"]
        for key, value in sorted(properties.items()):
            lines.append(f"  {key}: {value};")
        lines.append("}")
        
        return "\n".join(lines)
    
    def get_css_link(self):
        """Get inline style tag with theme CSS."""
        css = self.get_css()
        return f"<style>{css}</style>"
    
    def compile_theme_to_css(self):
        """
        Compile theme XML to full CSS file.
        Useful for static generation.
        """
        if not self.theme:
            return ""
        return self._properties_to_css(self.theme.get_all_properties())
    
    def get_color(self, color_name):
        """Get a specific color from theme."""
        if not self.theme:
            return None
        
        colors = self.theme.get_colors()
        return colors.get(color_name)
    
    def get_font_family(self):
        """Get primary font family."""
        if not self.theme:
            return None
        
        typography = self.theme.get_typography()
        return typography.get('font-family-primary')
    
    def clear_cache(self):
        """Clear cached CSS for this shop."""
        if self.shop:
            cache_key = f'theme_css_shop_{self.shop.id}'
        else:
            cache_key = 'theme_css_default'
        
        cache.delete(cache_key)


class ThemeCompiler:
    """
    Compiles themes to static CSS files.
    Used for optimization and offline support.
    """
    
    @staticmethod
    def compile_all_themes():
        """Compile all active themes to CSS files."""
        themes = Theme.objects.filter(is_active=True)
        compiled = {}
        
        for theme in themes:
            engine = ThemeEngine()
            engine.theme = theme
            css = engine.compile_theme_to_css()
            compiled[theme.name] = css
        
        return compiled
    
    @staticmethod
    def compile_shop_themes():
        """Compile CSS for all shop-specific themes."""
        from mydak.models import Shop
        
        shops = Shop.objects.filter(is_active=True)
        compiled = {}
        
        for shop in shops:
            engine = ThemeEngine(shop)
            css = engine.get_css()
            compiled[f'shop-{shop.id}'] = css
        
        return compiled
