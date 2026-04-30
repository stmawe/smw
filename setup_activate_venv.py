import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Use system python3 with venv activated approach
script = """cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python
source venv/bin/activate
python << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

import django
django.setup()

from django_tenants.models import Client, Domain

# Create tenant
tenant, tcr = Client.objects.get_or_create(
    schema_name='smw_main',
    defaults={'name': 'SMW Main'}
)
print(f'Tenant: {tenant.name} (created={tcr})')

# Create domain
domain, dcr = Domain.objects.get_or_create(
    domain='smw.pgwiz.cloud',
    defaults={'client': tenant, 'is_primary': True}
)
print(f'Domain: {domain.domain} (created={dcr})')
PYEOF
"""

print('Creating tenant with venv activation...')
stdin, stdout, stderr = client.exec_command(script)
output = stdout.read().decode()
errors = stderr.read().decode()

print('OUTPUT:')
print(output if output else '(no output)')

if errors:
    print('\nERRORS:')
    print(errors[:500])

client.close()
