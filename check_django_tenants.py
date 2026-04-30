import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Use Django shell to check tenants
print('=== CHECKING TENANTS VIA DJANGO ===')
cmd = """cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python && python manage.py shell << 'PYEND'
from django.contrib.sites.models import Site
from django_tenants.models import Client, Domain

print("Clients:", list(Client.objects.values_list('id', 'name', 'schema_name')))
print("Domains:", list(Domain.objects.values_list('domain', 'client_id')))
print("Sites:", list(Site.objects.values_list('id', 'domain', 'name')))
PYEND
"""

stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode()[-1000:])
print(stderr.read().decode()[-500:])

client.close()
