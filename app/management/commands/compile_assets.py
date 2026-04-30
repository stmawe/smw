"""Static asset pipeline management."""

import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class AssetPipeline:
    """Manages static assets for themes and components."""
    
    @staticmethod
    def compile_component_styles():
        """Compile component CSS from template styles."""
        components_dir = Path(settings.BASE_DIR) / 'templates' / 'components'
        
        styles = []
        
        # Extract styles from component templates
        for component_file in components_dir.glob('*.html'):
            if component_file.name.startswith('_'):
                continue
            
            content = component_file.read_text()
            
            # Extract <style> tags
            import re
            style_tags = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
            
            for style in style_tags:
                styles.append(f"/* {component_file.name} */\n{style}\n")
        
        return '\n'.join(styles)
    
    @staticmethod
    def generate_css_bundle():
        """Generate bundled CSS."""
        component_css = AssetPipeline.compile_component_styles()
        
        bundle = f"""/* UniMarket Component Library */
{component_css}
"""
        
        return bundle
    
    @staticmethod
    def minify_css(css_content):
        """Minify CSS content."""
        import re
        
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r'\s*([{}:;,>+])\s*', r'\1', css_content)
        
        return css_content.strip()


class Command(BaseCommand):
    """Django management command for static asset pipeline."""
    
    help = 'Compile and manage static assets'
    
    def add_arguments(self, parser):
        parser.add_argument('--compile', action='store_true', help='Compile all assets')
        parser.add_argument('--minify', action='store_true', help='Minify CSS/JS')
    
    def handle(self, *args, **options):
        if options['compile']:
            self.stdout.write('Compiling assets...')
            bundle = AssetPipeline.generate_css_bundle()
            
            output_dir = Path(settings.BASE_DIR) / 'static' / 'css'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / 'components.css'
            output_path.write_text(bundle)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created {output_path}'))
        
        if options['minify']:
            self.stdout.write('Minifying assets...')
            bundle = AssetPipeline.generate_css_bundle()
            minified = AssetPipeline.minify_css(bundle)
            
            output_dir = Path(settings.BASE_DIR) / 'static' / 'css'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / 'components.min.css'
            output_path.write_text(minified)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created {output_path}'))
