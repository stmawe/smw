import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Create management command
cmd_code = """import os
import sys
sys.path.insert(0, '/usr/home/wiptech/domains/smw.pgwiz.cloud/public_python')
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

# Check
print(f'Total clients: {Client.objects.count()}')
print(f'Total domains: {Domain.objects.count()}')
"""

# Write to server
cmd = f"cat > /tmp/setup.py << 'SETUPEOF'\n{cmd_code}\nSETUPEOF"
stdin, stdout, stderr = client.exec_command(cmd)
stdout.channel.recv_exit_status()

# Run it
print('Creating tenant...')
stdin, stdout, stderr = client.exec_command('cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python && /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/venv/bin/python /tmp/setup.py')
output = stdout.read().decode()
errors = stderr.read().decode()

print('OUTPUT:')
print(output)

if errors:
    print('\nERRORS:')
    print(errors[:800])

client.close()
