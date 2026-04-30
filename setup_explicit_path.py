import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Explicit path
proj_path = '/usr/home/wiptech/domains/smw.pgwiz.cloud/public_python'

script = f"""export PYTHONPATH={proj_path}
export DJANGO_SETTINGS_MODULE=config.settings.prod
cd {proj_path}
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '{proj_path}')
os.chdir('{proj_path}')

import django
django.setup()

from django_tenants.models import Client, Domain

t, tc = Client.objects.get_or_create(schema_name='smw_main', defaults={{'name': 'SMW Main'}})
print(f'Tenant: {{t.name}} (created={{tc}})')

d, dc = Domain.objects.get_or_create(domain='smw.pgwiz.cloud', defaults={{'client': t, 'is_primary': True}})
print(f'Domain: {{d.domain}} (created={{dc}})')

print(f'Total: {{Client.objects.count()}} clients, {{Domain.objects.count()}} domains')
PYEOF
"""

print('Setting up tenant...')
stdin, stdout, stderr = client.exec_command(script)
output = stdout.read().decode()
errors = stderr.read().decode()

print('OUTPUT:', output if output else '(none)')
if errors:
    print('ERRORS:', errors[:400])

client.close()
