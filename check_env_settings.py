import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

print('=== .ENV FILE ===')
stdin, stdout, stderr = client.exec_command('cat /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/.env')
print(stdout.read().decode())

print('\n=== BASE SETTINGS (first 50 lines) ===')
stdin, stdout, stderr = client.exec_command('head -50 /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/config/settings/base.py | tail -30')
print(stdout.read().decode())

client.close()
