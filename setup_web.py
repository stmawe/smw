import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('128.204.223.70', username='wiptech', password='93SVrso1cMYn')

# Create public_html
client.exec_command('mkdir -p /usr/home/wiptech/domains/smw.pgwiz.cloud/public_html')

# Create a simple index file
cmd = """cat > /usr/home/wiptech/domains/smw.pgwiz.cloud/public_html/index.html << 'EOFINDEX'
<!DOCTYPE html>
<html>
<head>
<title>Django App</title>
</head>
<body>
<h1>Django application is running</h1>
<p>Check /dashboard/ for admin access</p>
</body>
</html>
EOFINDEX"""

stdin, stdout, stderr = client.exec_command(cmd)
print("index.html created")

# Check if there's an app.py or wsgi entry point needed
print("\nChecking config:")
stdin, stdout, stderr = client.exec_command('ls -la /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/ | head -20')
for line in stdout.read().decode().split('\n')[:20]:
    print(line)

# For Passenger/Python, we need to either:
# 1. Have a public/ folder with static files
# 2. Configure Passenger to use WSGI

print("\n\nCreating public folder:")
client.exec_command('mkdir -p /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/public')

# Run Django collectstatic
print("Running collectstatic...")
stdin, stdout, stderr = client.exec_command('cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python && python manage.py collectstatic --noinput 2>&1 | tail -5')
print(stdout.read().decode())

client.close()
