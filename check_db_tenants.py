import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Check tenants via psql
print('Checking tenants in database...')
cmd = """psql -h pgsql3.serv00.com -U p7152_smw -d p7152_smw -c "SELECT id, name, schema_name FROM public.tenant_client LIMIT 5;" 2>&1"""
stdin, stdout, stderr = client.exec_command(cmd)

output = stdout.read().decode()
print(output)

# Check domains
print('\nChecking domains in database...')
cmd = """psql -h pgsql3.serv00.com -U p7152_smw -d p7152_smw -c "SELECT domain, client_id, is_primary FROM public.tenant_domain;" 2>&1"""
stdin, stdout, stderr = client.exec_command(cmd)

output = stdout.read().decode()
print(output)

client.close()
