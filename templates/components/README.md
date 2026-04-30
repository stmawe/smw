"""
UniMarket Component Library

All reusable UI components are defined in templates/components/ and follow
a consistent design system using CSS custom properties from the theme.

## Available Components

### Button (`components/button.html`)
Renders a button with optional styling and states.

Context variables:
- `button_text` (str, required): Button label
- `button_class` (str): CSS class (btn-primary, btn-secondary, btn-success, etc.)
- `button_disabled` (bool): Whether button is disabled
- `button_type` (str): HTML button type (button, submit, reset)

Example:
```django
{% include "components/button.html" with button_text="Click Me" button_class="btn-primary" %}
```

### Card (`components/card.html`)
Renders a card container with optional header and footer.

Context variables:
- `card_content` (str, required): Card body content
- `card_header` (str): Optional header text
- `card_footer` (str): Optional footer text
- `card_class` (str): Additional CSS classes (e.g., card-elevated)

Example:
```django
{% include "components/card.html" with card_header="Title" card_content="Content here" %}
```

### Form Group (`components/form_group.html`)
Renders a form field with label and validation.

Context variables:
- `form_label` (str): Field label
- `form_id` (str): Field ID
- `form_name` (str): Field name
- `form_type` (str): Input type (text, email, password, etc.)
- `form_placeholder` (str): Placeholder text
- `form_required` (bool): Whether field is required
- `form_hint` (str): Help text below field
- `form_value` (str): Current field value
- `form_choices` (list): For select fields

Example:
```django
{% include "components/form_group.html" with form_label="Email" form_type="email" form_required=True %}
```

### Messages (`components/messages.html`)
Renders Django messages using theme colors.

Usage:
```django
{% include "components/messages.html" %}
```

## Design System

All components use CSS custom properties for theming:
- Colors: `--theme-colors-*`
- Typography: `--theme-typography-*`
- Spacing: `--theme-spacing-*`
- Borders: `--theme-borders-*`
- Shadows: `--theme-shadows-*`
- Animations: `--theme-animations-*`

See apps/themes/xml_spec.py for complete list of available variables.

## Component Rules

1. **Always use theme variables** - Never hardcode colors, spacing, or sizing
2. **Semantic HTML** - Use proper HTML elements (button, form, section, etc.)
3. **Accessibility** - Include labels, ARIA attributes, keyboard support
4. **Responsive design** - Use flexbox/grid with theme spacing units
5. **No external dependencies** - Pure CSS (no Bootstrap, Tailwind, etc.)
6. **Self-contained CSS** - Include styling in the template using <style> tags
7. **State management** - Support disabled, error, loading states
8. **Consistent naming** - Use BEM-like class naming (.component-element)

## Component Variants

Each component supports variants through context variables:
- Size variants: `size=small|normal|large`
- State variants: `disabled=True`, `error=True`, `loading=True`
- Style variants: `variant=primary|secondary|outline|ghost`
- Layout variants: `full_width=True`, `inline=True`

Example:
```django
{% include "components/button.html" with button_text="Delete" button_class="btn-danger btn-small" button_disabled=True %}
```

## Future Components

Planned components for Phase 7.2:
- Alert box
- Badge
- Breadcrumb
- Dropdown menu
- Modal dialog
- Pagination
- Progress bar
- Sidebar
- Tabs
- Tooltip
- Rating stars
- Image gallery
- Search box
- Filter controls
"""
