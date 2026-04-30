# 🎨 Theme System - Design Mode Configuration

The SMW platform now supports **database-driven theming** with admin design mode capabilities. This allows admins to:

- ✅ Create custom themes with design token overrides
- ✅ Apply different themes to different pages (page-specific theming)
- ✅ Mock component designs before deployment
- ✅ Change colors, fonts, spacing via admin panel (no code changes needed)
- ✅ Maintain audit trail of all design changes
- ✅ Create design variants and switch between them instantly

## 🚀 Quick Start

### 1. Initialize Default Theme Tokens

Run this once to set up the design system tokens:

```bash
python manage.py migrate  # Create theme tables
python manage.py init_theme_tokens  # Add default tokens
```

### 2. Access Theme Admin

Go to `/admin/app/theme/` to manage themes:
- **Create themes** with name, slug, and description
- **Override tokens** - change colors, fonts, spacing values
- **Add custom CSS** - write additional CSS rules
- **Activate theme** - make it the default for the site

### 3. Page-Specific Themes

Go to `/admin/app/pagethemeassignment/` to assign:
- Homepage → "Hero Theme" 
- Admin Dashboard → "Dark Professional"
- Explore Page → "Vibrant Marketplace"

## 📋 Model Architecture

### ThemeToken
Individual design tokens that can be overridden:
- **Colors**: `--blue-500`, `--gold-400`, `--green-400`
- **Typography**: `--font-display`, `--font-body`, `--font-mono`
- **Spacing**: `--space-1` through `--space-9`
- **Effects**: `--glass-blur`, `--glow-blue`, shadows

```python
# Example token
ThemeToken.objects.create(
    name='primary-blue',
    category='color',
    default_value='#1A72E8',
    css_custom_property='--color-primary',
    description='Primary action blue across site'
)
```

### Theme
Collection of token overrides that can be activated:

```python
# Example theme
theme = Theme.objects.create(
    name='Dark Luxury',
    slug='dark-luxury',
    theme_type='global',
    token_overrides={
        'blue-500': '#2563EB',  # Override specific tokens
        'gold-400': '#F0CA70',
    },
    custom_css="""
    .hero {
        background: linear-gradient(135deg, var(--blue-800), var(--blue-900));
    }
    """,
    is_active=True  # Make active
)
```

### PageThemeAssignment
Maps pages to specific themes:

```python
PageThemeAssignment.objects.create(
    page_type='homepage',
    theme=my_homepage_theme,
    override_enabled=True
)
```

### ThemeComponentLibrary
Reusable components with versioning for design mocking:

```python
component = ThemeComponentLibrary.objects.create(
    name='NavBar',
    slug='navbar',
    version=1,
    is_draft=True,  # Mock version
    html_template='<nav>...</nav>',
    inline_css='/* Component CSS */',
    theme=my_theme
)

# When ready to deploy, call:
component.publish()  # Marks old versions as unpublished
```

### ThemeChangeLog
Audit trail of all theme modifications:
- Who changed what
- When it changed
- Why it changed (reason field)
- Old vs new values stored as JSON

## 🎯 Design Mode Workflow

### For Admins Creating New Themes

1. **Go to `/admin/app/theme/`** → Add new theme
2. **Fill in basic info**: Name, slug, theme type
3. **Override tokens** - Edit `token_overrides` JSON field
   ```json
   {
     "blue-500": "#2563EB",
     "gold-400": "#F0CA70",
     "space-4": "18px"
   }
   ```
4. **Add custom CSS** - Override specific component styles
5. **Test** - Visit site, theme CSS injects automatically
6. **Activate** - Check `is_active` checkbox
7. **Assign to pages** - Use PageThemeAssignment for page-specific overrides

### For Component Development

1. **Create draft component** - `ThemeComponentLibrary` with `is_draft=True`
2. **Edit HTML/CSS/JS** - Design and iterate
3. **Preview** - Use query param to select component version for testing
4. **Publish** - Call `.publish()` method, automatically marks as live
5. **Revert** - Old versions still in database, can reactivate

## 🔧 Template Integration

### Automatic Theme Injection

The context processor automatically injects theme CSS into all templates:

```html
<!-- In base.html or home_base.html -->
<style>
    {{ theme_css|safe }}
</style>
```

This renders the merged tokens + custom CSS for the active (or page-specific) theme.

### Programmatic Access in Views

```python
from app.theme_utils import get_theme_for_page, generate_theme_css

# Get theme for specific page
theme = get_theme_for_page('homepage')

# Generate CSS for that theme
css = generate_theme_css(theme)

# In context data
context = {
    'current_theme': theme,
    'theme_css': css,
}
```

## 📝 CSS Custom Properties

All design values use CSS custom properties for easy overriding:

```css
/* Before: Hardcoded values */
.button {
  background-color: #1A72E8;
  padding: 16px;
  font-family: 'Sora', sans-serif;
}

/* After: Themeable values */
.button {
  background-color: var(--color-primary);
  padding: var(--space-4);
  font-family: var(--font-body);
}
```

When a theme overrides `--color-primary` to `#2563EB`, all buttons automatically update.

## 🚀 Advanced Features

### Creating a Light Theme from Dark Theme

```python
light_theme = Theme.objects.create(
    name='Light Enterprise',
    slug='light-enterprise',
    token_overrides={
        'surface-0': '#F5F7FA',
        'surface-1': '#FFFFFF',
        'text-1': '#1F2937',
        'text-2': '#4B5563',
    }
)
```

### Accessibility Mode Theme

```python
a11y_theme = Theme.objects.create(
    name='High Contrast',
    slug='high-contrast',
    theme_type='accessibility',
    token_overrides={
        'text-1': '#000000',
        'surface-0': '#FFFFFF',
        'border-hi': 'rgba(0, 0, 0, 0.3)',
    },
    custom_css="""
    * {
        font-size: 18px !important;
    }
    button, a {
        border: 2px solid var(--color-primary) !important;
    }
    """
)
```

### Caching

Theme CSS is cached for 1 hour per theme to reduce database queries:

```python
from django.core.cache import cache

# Manually clear cache
cache.delete('active_theme_css')
cache.delete('theme_css_123')  # theme id 123
```

## 🔐 Admin Interface Security

- **Read-only changelog** - Cannot edit past changes (audit trail)
- **User attribution** - All changes tracked with `created_by` user
- **Change reasons** - Document why changes were made
- **Activation control** - Only one theme active at a time (enforced in model.save())

## 📱 Mobile-First Component Variants

Create mobile-specific theme overrides:

```python
mobile_theme = Theme.objects.create(
    name='Mobile Optimized',
    slug='mobile-optimized',
    custom_css="""
    @media (max-width: 768px) {
        :root {
            --space-4: 14px;  /* Reduce padding on mobile
        }
        .navbar {
            display: none;
        }
        .mobile-menu {
            display: block;
        }
    }
    """
)
```

## ✅ Testing Theme Changes

After creating a theme:

1. **Activate in admin** - Check `is_active`
2. **Visit homepage** - CSS should update automatically
3. **Inspect element** - Look for `:root { --variable: value; }`
4. **Check console** - No errors should appear
5. **Test across pages** - If page-specific themes assigned

## 🚀 Deployment Notes

- Theme tokens stored in database (survives migrations/deploys)
- Context processor caches CSS for performance
- Change log records all modifications (for review/audit)
- Safe to modify themes without restarting Django
- CSS injection happens at template render time
