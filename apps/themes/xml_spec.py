"""
XML Theme Specification for UniMarket

UniMarket themes are defined in XML with the following structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<theme id="light" version="1.0" author="UniMarket">
    <meta>
        <name>Light Theme</name>
        <description>Default light theme</description>
        <requires-version>1.0</requires-version>
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
        <font-family-primary>-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto</font-family-primary>
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
        <radius-small>4px</radius-small>
        <radius-medium>8px</radius-medium>
        <radius-large>12px</radius-large>
        <width>1px</width>
        <width-thick>2px</width-thick>
    </borders>
    
    <shadows>
        <shadow-sm>0 1px 2px rgba(0, 0, 0, 0.05)</shadow-sm>
        <shadow-md>0 2px 10px rgba(0, 0, 0, 0.1)</shadow-md>
        <shadow-lg>0 10px 25px rgba(0, 0, 0, 0.2)</shadow-lg>
    </shadows>
    
    <animations>
        <duration-fast>100ms</duration-fast>
        <duration-normal>300ms</duration-normal>
        <duration-slow>500ms</duration-slow>
        <easing-ease>ease</easing-ease>
        <easing-ease-in>ease-in</easing-ease-in>
        <easing-ease-out>ease-out</easing-ease-out>
        <easing-ease-in-out>ease-in-out</easing-ease-in-out>
    </animations>
    
    <custom-properties>
        <property name="navbar-height">60px</property>
        <property name="sidebar-width">280px</property>
        <property name="card-elevation">2px</property>
    </custom-properties>
</theme>
```

Key Elements:
- `id`: Theme identifier (must be unique)
- `version`: Semantic version
- `colors`: CSS color variables
- `typography`: Font sizes, families, line heights
- `spacing`: Unit-based spacing system
- `borders`: Radius, width, and border styles
- `shadows`: Elevation shadows
- `animations`: Timing functions and durations
- `custom-properties`: Shop-specific overrides

Variable Reference in CSS:
Variables are injected as CSS custom properties in the format: --theme-{element}-{property}

Example:
- --theme-colors-primary: #667eea
- --theme-typography-font-family-primary: -apple-system, ...
- --theme-spacing-unit: 8px
- --theme-custom-navbar-height: 60px
"""
