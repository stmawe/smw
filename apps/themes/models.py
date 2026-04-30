"""Theme models."""

from django.db import models
from apps.core.models import TimeStampedModel
import xml.etree.ElementTree as ET
import json


class Theme(TimeStampedModel):
    """
    Stores theme definitions (either XML or JSON).
    Themes are shop-specific and can be based on built-ins.
    """
    
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    
    # Theme definition (XML format)
    definition = models.TextField(
        help_text="XML theme definition"
    )
    
    # Metadata
    version = models.CharField(max_length=10, default='1.0')
    author = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_built_in = models.BooleanField(default=False, help_text="Built-in theme, read-only")
    
    # Preview
    preview_image = models.ImageField(upload_to='theme-previews/', null=True, blank=True)
    
    class Meta:
        ordering = ['-is_built_in', 'name']
        indexes = [
            models.Index(fields=['is_active', 'is_built_in']),
        ]
        verbose_name = 'Theme'
        verbose_name_plural = 'Themes'
    
    def __str__(self):
        return self.name
    
    def parse_xml(self):
        """Parse XML definition and return element tree."""
        try:
            return ET.fromstring(self.definition)
        except ET.ParseError as e:
            raise ValueError(f"Invalid theme XML: {str(e)}")
    
    def get_colors(self):
        """Extract colors from theme."""
        try:
            root = self.parse_xml()
            colors = root.find('colors')
            if colors is None:
                return {}
            
            return {
                child.tag: child.text
                for child in colors
                if child.text
            }
        except Exception:
            return {}
    
    def get_typography(self):
        """Extract typography settings from theme."""
        try:
            root = self.parse_xml()
            typography = root.find('typography')
            if typography is None:
                return {}
            
            return {
                child.tag: child.text
                for child in typography
                if child.text
            }
        except Exception:
            return {}
    
    def get_spacing(self):
        """Extract spacing settings from theme."""
        try:
            root = self.parse_xml()
            spacing = root.find('spacing')
            if spacing is None:
                return {}
            
            return {
                child.tag: child.text
                for child in spacing
                if child.text
            }
        except Exception:
            return {}
    
    def get_all_properties(self):
        """Get all theme properties as CSS custom properties."""
        properties = {}
        
        # Colors
        colors = self.get_colors()
        for key, value in colors.items():
            properties[f'--theme-colors-{key}'] = value
        
        # Typography
        typography = self.get_typography()
        for key, value in typography.items():
            properties[f'--theme-typography-{key}'] = value
        
        # Spacing
        spacing = self.get_spacing()
        for key, value in spacing.items():
            properties[f'--theme-spacing-{key}'] = value
        
        return properties


class ShopTheme(TimeStampedModel):
    """
    Maps themes to shops.
    Allows per-shop theme customization.
    """
    
    shop = models.OneToOneField(
        'mydak.Shop',
        on_delete=models.CASCADE,
        related_name='theme_config'
    )
    theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shop_themes'
    )
    
    # Custom overrides (JSON)
    custom_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom CSS property overrides as JSON"
    )
    
    # Enable theme system
    enabled = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Shop Theme'
        verbose_name_plural = 'Shop Themes'
    
    def __str__(self):
        return f"{self.shop.name} - {self.theme.name if self.theme else 'Default'}"
    
    def get_css_properties(self):
        """
        Get all CSS custom properties for this shop.
        Merges theme properties with custom overrides.
        """
        properties = {}
        
        if self.theme:
            properties.update(self.theme.get_all_properties())
        
        # Apply custom overrides
        if self.custom_overrides:
            properties.update(self.custom_overrides)
        
        return properties
    
    def get_css_string(self):
        """Get CSS custom properties as a CSS rule."""
        properties = self.get_css_properties()
        
        if not properties:
            return ""
        
        lines = [":root {"]
        for key, value in sorted(properties.items()):
            lines.append(f"  {key}: {value};")
        lines.append("}")
        
        return "\n".join(lines)
