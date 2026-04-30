import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Read local advanced passenger_wsgi.py
with open('passenger_wsgi.py', 'r') as f:
    wsgi_content = f.read()

# Upload to server
cmd = f"cat > /usr/home/wiptech/domains/smw.pgwiz.cloud/passenger_wsgi.py << 'WSGIEOF'\n{wsgi_content}\nWSGIEOF"
stdin, stdout, stderr = client.exec_command(cmd)
exit_code = stdout.channel.recv_exit_status()

if exit_code == 0:
    print('✓ Advanced passenger_wsgi.py uploaded to server')
else:
    print('✗ Failed to upload')

# Verify
stdin, stdout, stderr = client.exec_command('head -10 /usr/home/wiptech/domains/smw.pgwiz.cloud/passenger_wsgi.py')
print('\nServer file (first 10 lines):')
print(stdout.read().decode())

# Set permissions
stdin, stdout, stderr = client.exec_command('chmod 644 /usr/home/wiptech/domains/smw.pgwiz.cloud/passenger_wsgi.py && ls -la /usr/home/wiptech/domains/smw.pgwiz.cloud/passenger_wsgi.py')
print('\nPermissions:')
print(stdout.read().decode())

client.close()
