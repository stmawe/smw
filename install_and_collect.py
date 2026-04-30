import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

print('Installing requirements...')
stdin, stdout, stderr = client.exec_command('cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python && pip install -r requirements.txt')
exit_code = stdout.channel.recv_exit_status()
print(f"pip install exit code: {exit_code}")

print('\nRunning collectstatic...')
stdin, stdout, stderr = client.exec_command('cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python && python manage.py collectstatic --noinput')
output = stdout.read().decode()
print(output[-500:] if len(output) > 500 else output)

print('\nStatic files location:')
stdin, stdout, stderr = client.exec_command('test -d /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/public && echo EXISTS || echo MISSING')
print(stdout.read().decode())

client.close()
