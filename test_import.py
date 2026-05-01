import sys
import os
sys.path.insert(0, '/usr/home/wiptech/domains/smw.pgwiz.cloud/public_python')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

try:
    import django
    django.setup()
    print("Django setup OK")
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

try:
    from app.admin_urls import admin_subdomain_patterns
    print(f"Import successful: {len(admin_subdomain_patterns)} patterns")
    for pattern in admin_subdomain_patterns:
        print(f"  - {pattern.pattern}")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
