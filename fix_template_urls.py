#!/usr/bin/env python
"""
Fix template URL references from 'admin:name' format to actual URL pattern names
"""
import os
import re
from pathlib import Path

# Mapping from template reference to actual URL pattern name
URL_MAPPING = {
    'admin:users': 'admin_users_list',
    'admin:shops': 'admin_shops_list',
    'admin:listings': 'admin_listings_list',
    'admin:analytics': 'admin_analytics_dashboard',
    'admin:settings': 'admin_settings',
    'admin:moderation': 'admin_moderation_center',
    'admin:activity': 'admin_activity_feed',
    'admin:user-create': 'admin_user_create',
    'admin:user-detail': 'admin_user_detail',
    'admin:shop-detail': 'admin_shop_detail',
    'admin:shop-create': 'admin_shop_create',
    'admin:shop-ssl': 'admin_shop_ssl',
    'admin:shop-listings': 'admin_shop_listings',
    'admin:shop-analytics': 'admin_shop_analytics',
    'admin:listing-detail': 'admin_listing_detail',
    'admin:transaction-detail': 'admin_transaction_detail',
}

template_dir = Path('templates/admin')
updated_files = 0
total_replacements = 0

for template_file in template_dir.rglob('*.html'):
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace all URL references - handle both single and double quotes
    for old_ref, new_ref in URL_MAPPING.items():
        old_pattern_single = f"'{old_ref}'"
        old_pattern_double = f'"{old_ref}"'
        new_pattern = f"'{new_ref}'"
        
        if old_pattern_single in content:
            content = content.replace(old_pattern_single, new_pattern)
            print(f"  Found and replacing: {old_pattern_single} → {new_pattern}")
        
        if old_pattern_double in content:
            content = content.replace(old_pattern_double, new_pattern)
            print(f"  Found and replacing: {old_pattern_double} → {new_pattern}")
    
    if content != original_content:
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Updated: {template_file.relative_to(template_dir.parent)}")
        updated_files += 1

print(f"\n✓ Updated {updated_files} template files")
