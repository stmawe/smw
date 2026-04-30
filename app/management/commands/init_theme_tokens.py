"""
Django management command to initialize theme system with default tokens.
Run once: python manage.py init_theme_tokens

This creates all the design system tokens that can be overridden per theme.
"""

from django.core.management.base import BaseCommand
from app.models import ThemeToken


DEFAULT_TOKENS = [
    # Colors
    ('blue-950', 'color', '#020A1A', '--blue-950', 'Near-black navy background'),
    ('blue-900', 'color', '#061428', '--blue-900', 'Deep navy section background'),
    ('blue-800', 'color', '#0A2240', '--blue-800', 'Dark navy card background'),
    ('blue-500', 'color', '#1A72E8', '--blue-500', 'Primary action blue'),
    ('blue-400', 'color', '#4A94F0', '--blue-400', 'Hover blue'),
    ('gold-400', 'color', '#E8B030', '--gold-400', 'Primary accent gold'),
    ('gold-300', 'color', '#F0CA70', '--gold-300', 'Light gold hover'),
    ('green-400', 'color', '#26B857', '--green-400', 'Success green'),
    ('surface-0', 'color', '#020B1C', '--surface-0', 'Page background'),
    ('surface-1', 'color', '#071830', '--surface-1', 'Elevated surface'),
    ('surface-2', 'color', '#0C2540', '--surface-2', 'Card surface'),
    ('text-1', 'color', '#F2F7FF', '--text-1', 'Primary text color'),
    ('text-2', 'color', '#A8BDD8', '--text-2', 'Secondary text color'),
    ('text-3', 'color', '#5C7A99', '--text-3', 'Muted text color'),
    
    # Typography
    ('font-display', 'typography', "'Canela', 'Georgia', serif", '--font-display', 'Display font family'),
    ('font-body', 'typography', "'Sora', sans-serif", '--font-body', 'Body text font family'),
    ('font-mono', 'typography', "'JetBrains Mono', monospace", '--font-mono', 'Monospace font'),
    
    # Spacing
    ('space-1', 'spacing', '4px', '--space-1', 'Extra small spacing'),
    ('space-2', 'spacing', '8px', '--space-2', 'Small spacing'),
    ('space-3', 'spacing', '12px', '--space-3', 'Base spacing'),
    ('space-4', 'spacing', '16px', '--space-4', 'Medium spacing'),
    ('space-5', 'spacing', '24px', '--space-5', 'Large spacing'),
    ('space-6', 'spacing', '32px', '--space-6', 'Extra large spacing'),
    ('space-7', 'spacing', '48px', '--space-7', 'Huge spacing'),
    
    # Border Radius
    ('radius-sm', 'radius', '6px', '--radius-sm', 'Small border radius'),
    ('radius-md', 'radius', '10px', '--radius-md', 'Medium border radius'),
    ('radius-lg', 'radius', '16px', '--radius-lg', 'Large border radius'),
    ('radius-pill', 'radius', '9999px', '--radius-pill', 'Pill/circle border radius'),
    
    # Shadows
    ('shadow-card', 'shadow', '0 4px 24px rgba(2, 10, 26, 0.6), 0 1px 0 rgba(255,255,255,0.04) inset', '--shadow-card', 'Card shadow'),
    ('shadow-md', 'shadow', '0 8px 32px rgba(2, 10, 26, 0.8), 0 2px 0 rgba(255,255,255,0.06) inset', '--shadow-md', 'Medium shadow'),
    
    # Effects
    ('glass-blur', 'effect', 'blur(16px)', '--glass-blur', 'Glassmorphism blur'),
    ('glow-blue', 'effect', '0 0 40px rgba(26, 114, 232, 0.25)', '--glow-blue', 'Blue glow effect'),
    ('glow-gold', 'effect', '0 0 40px rgba(232, 176, 48, 0.20)', '--glow-gold', 'Gold glow effect'),
]


class Command(BaseCommand):
    help = 'Initialize default theme design tokens'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎨 Initializing theme tokens...'))
        
        created_count = 0
        for name, category, value, css_prop, description in DEFAULT_TOKENS:
            token, created = ThemeToken.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'default_value': value,
                    'css_custom_property': css_prop,
                    'description': description,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created {css_prop}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} theme tokens'))
