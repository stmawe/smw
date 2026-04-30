import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

print('DOMAIN ROOT:')
stdin, stdout, stderr = client.exec_command('ls -la /usr/home/wiptech/domains/smw.pgwiz.cloud/')
print(stdout.read().decode()[:800])

print('\n\nDEVIL DOMAIN CONFIG:')
stdin, stdout, stderr = client.exec_command('devil www info smw.pgwiz.cloud')
print(stdout.read().decode())

print('\n\nWSGI CHECK:')
stdin, stdout, stderr = client.exec_command('test -f /usr/home/wiptech/domains/smw.pgwiz.cloud/smw/wsgi.py && echo WSGI_OK || echo WSGI_MISSING')
print(stdout.read().decode())

print('\n\nPUBLIC_HTML:')
stdin, stdout, stderr = client.exec_command('ls -la /usr/home/wiptech/domains/smw.pgwiz.cloud/public_html 2>/dev/null | head -5 || echo "NO public_html"')
print(stdout.read().decode())

print('\n\nNGINX CONFIG:')
stdin, stdout, stderr = client.exec_command('ls /etc/nginx/vhosts/smw.pgwiz.cloud* 2>/dev/null || echo "NO nginx config"')
print(stdout.read().decode())

client.close()
