#!/usr/bin/env python3
"""
Fix Django template syntax errors in admin templates.
Replace incorrect {% endinclude %} with proper closing tags.
"""

import os
import re

def fix_template_file(filepath):
    """Fix template syntax in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Pattern 1: {% include ... with ... %} followed by content and {% endinclude %}
    # Should be: {% include ... with ... %} then content then nothing (include doesn't need end tag)
    # The content between include and endinclude should be INSIDE the include tag or not there at all
    
    # For now, simply remove all {% endinclude %} tags since Django's include tag doesn't use them
    content = content.replace('{% endinclude %}', '')
    content = content.replace('{%endinclude%}', '')
    content = content.replace('{% endinclude%}', '')
    content = content.replace('{%endinclude %}', '')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, filepath
    return False, filepath

def main():
    template_dir = r'E:\Backup\pgwiz\smw\templates\admin'
    fixed_files = []
    
    # Walk through all HTML files
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                was_fixed, fname = fix_template_file(filepath)
                if was_fixed:
                    fixed_files.append(fname)
                    print(f"✓ Fixed: {fname}")
    
    print(f"\nTotal files fixed: {len(fixed_files)}")
    return len(fixed_files)

if __name__ == '__main__':
    main()
