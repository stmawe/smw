"""Built-in theme definitions."""

LIGHT_THEME = """<?xml version="1.0" encoding="UTF-8"?>
<theme id="light" version="1.0" author="UniMarket">
    <meta>
        <name>Light Theme</name>
        <description>Clean, minimal light theme</description>
    </meta>
    <colors>
        <primary>#667eea</primary>
        <primary-dark>#764ba2</primary-dark>
        <secondary>#f093fb</secondary>
        <success>#3c3</success>
        <warning>#ff9800</warning>
        <error>#c33</error>
        <info>#2196f3</info>
        <neutral>#999</neutral>
        <background>#fff</background>
        <surface>#f5f5f5</surface>
        <text>#333</text>
        <text-secondary>#666</text-secondary>
        <border>#ddd</border>
    </colors>
    <typography>
        <font-family-primary>-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif</font-family-primary>
        <font-family-mono>Monaco, Menlo, 'Ubuntu Mono', monospace</font-family-mono>
        <font-size-base>16px</font-size-base>
        <font-size-small>14px</font-size-small>
        <font-size-large>18px</font-size-large>
        <line-height-base>1.5</line-height-base>
    </typography>
    <spacing>
        <unit>8px</unit>
        <gap-small>4px</gap-small>
        <gap-medium>8px</gap-medium>
        <gap-large>16px</gap-large>
        <gap-xlarge>24px</gap-xlarge>
    </spacing>
    <borders>
        <radius-small>6px</radius-small>
        <radius-medium>10px</radius-medium>
        <radius-large>16px</radius-large>
        <radius-pill>9999px</radius-pill>
    </borders>
    <shadows>
        <shadow-card>0 4px 24px rgba(2, 10, 26, 0.10)</shadow-card>
        <shadow-md>0 8px 32px rgba(2, 10, 26, 0.16)</shadow-md>
    </shadows>
    <animations>
        <duration-fast>100ms</duration-fast>
        <duration-normal>240ms</duration-normal>
        <duration-slow>420ms</duration-slow>
    </animations>
    <custom-properties>
        <property name="navbar-height">60px</property>
        <property name="sidebar-width">280px</property>
    </custom-properties>
</theme>"""

DARK_THEME = """<?xml version="1.0" encoding="UTF-8"?>
<theme id="dark" version="1.0" author="UniMarket">
    <meta>
        <name>Dark Theme</name>
        <description>Modern dark theme</description>
    </meta>
    <colors>
        <primary>#667eea</primary>
        <primary-dark>#5568d3</primary-dark>
        <secondary>#f093fb</secondary>
        <success>#3c3</success>
        <warning>#ff9800</warning>
        <error>#c33</error>
        <info>#2196f3</info>
        <neutral>#999</neutral>
        <background>#1a1a1a</background>
        <surface>#2a2a2a</surface>
        <text>#eee</text>
        <text-secondary>#999</text-secondary>
        <border>#444</border>
    </colors>
    <typography>
        <font-family-primary>-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif</font-family-primary>
        <font-family-mono>Monaco, Menlo, 'Ubuntu Mono', monospace</font-family-mono>
        <font-size-base>16px</font-size-base>
        <font-size-small>14px</font-size-small>
        <font-size-large>18px</font-size-large>
        <line-height-base>1.5</line-height-base>
    </typography>
    <spacing>
        <unit>8px</unit>
        <gap-small>4px</gap-small>
        <gap-medium>8px</gap-medium>
        <gap-large>16px</gap-large>
        <gap-xlarge>24px</gap-xlarge>
    </spacing>
    <borders>
        <radius-small>6px</radius-small>
        <radius-medium>10px</radius-medium>
        <radius-large>16px</radius-large>
        <radius-pill>9999px</radius-pill>
    </borders>
    <shadows>
        <shadow-card>0 4px 24px rgba(0, 0, 0, 0.38)</shadow-card>
        <shadow-md>0 8px 32px rgba(0, 0, 0, 0.52)</shadow-md>
    </shadows>
    <animations>
        <duration-fast>100ms</duration-fast>
        <duration-normal>240ms</duration-normal>
        <duration-slow>420ms</duration-slow>
    </animations>
    <custom-properties>
        <property name="navbar-height">60px</property>
        <property name="sidebar-width">280px</property>
    </custom-properties>
</theme>"""

BUILT_IN_THEMES = {
    'light': LIGHT_THEME,
    'dark': DARK_THEME,
}


def create_built_in_themes():
    """Create built-in themes in database."""
    from .models import Theme
    
    created = []
    
    for theme_id, definition in BUILT_IN_THEMES.items():
        theme, is_new = Theme.objects.get_or_create(
            name=theme_id,
            defaults={
                'definition': definition,
                'version': '1.0',
                'author': 'UniMarket',
                'is_built_in': True,
                'is_active': True,
                'description': f'Built-in {theme_id} theme',
            }
        )
        
        if is_new:
            created.append(theme)
    
    return created
