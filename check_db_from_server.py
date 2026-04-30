import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

print('=== CHECKING TENANTS FROM SERVER ===')

# Check tenants
cmd = "psql -h pgsql3.serv00.com -U p7152_smw -d p7152_smw -c \"SELECT id, name, schema_name FROM public.tenant_client LIMIT 5;\" 2>&1"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print('\n=== CHECKING DOMAINS FROM SERVER ===')
cmd = "psql -h pgsql3.serv00.com -U p7152_smw -d p7152_smw -c \"SELECT domain, client_id FROM public.tenant_domain LIMIT 10;\" 2>&1"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print('\n=== CHECKING SCHEMAS ===')
cmd = "psql -h pgsql3.serv00.com -U p7152_smw -d p7152_smw -c \"SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg_%' ORDER BY schema_name;\" 2>&1"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode()[:800])

client.close()
