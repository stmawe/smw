# Production Deployment Setup Guide

This guide walks through setting up the production deployment infrastructure on your server.

## Prerequisites

### Local Machine
- Python 3.7+
- paramiko library: `pip install paramiko`
- Git access to push changes (✅ already done)

### Production Server
- SSH access (credentials needed)
- PostgreSQL client installed
- Bash shell
- Cron daemon running

## Step 1: Install Paramiko Locally

```bash
pip install paramiko
```

## Step 2: Run Deploy Script

The `deploy.py` script handles all server-side setup automatically. Choose one of these options:

### Option A: Using Password Authentication

```bash
python deploy.py \
  --host YOUR_SERVER_HOSTNAME \
  --user root \
  --password YOUR_SSH_PASSWORD \
  --repo-path /home/wiptech/domains/smw.cyring.store/public_python \
  --push
```

Example for serv00 hosting:
```bash
python deploy.py \
  --host serv00.example.com \
  --user root \
  --password your_password_here \
  --push
```

### Option B: Using SSH Key

```bash
python deploy.py \
  --host YOUR_SERVER_HOSTNAME \
  --user root \
  --key ~/.ssh/id_rsa \
  --repo-path /home/wiptech/domains/smw.cyring.store/public_python
```

### Option C: Verify Setup Without Making Changes

```bash
python deploy.py \
  --host YOUR_SERVER_HOSTNAME \
  --user root \
  --password YOUR_SSH_PASSWORD \
  --verify-only
```

## Step 3: What the Script Does

The `deploy.py` script automatically:

1. **Connects to server** via SSH
2. **Checks for .env file**:
   - If exists: Uses current configuration
   - If missing: Creates with fallback credentials:
     - DB_HOST: pgsql3.serv00.com
     - DB_NAME: p7152_smw
     - DB_USER: p7152_smw
     - DB_PASS: LUGLsxDp7ptf
3. **Verifies update script** (`scripts/update_site.sh`):
   - Checks it exists
   - Makes it executable
4. **Creates directories**:
   - `/path/to/repo/logs/deployment/` - For deployment logs
   - `/path/to/repo/.backups/` - For backup files
5. **Sets up cron job**:
   - Adds entry to run every 2 hours
   - Cron entry: `0 */2 * * * cd /repo/path && bash scripts/update_site.sh >> logs/deployment/cron.log 2>&1`
6. **(Optional) Pushes to GitHub** if `--push` flag used

## Step 4: Verify Deployment

After running the script successfully:

### Check Cron Job on Server

```bash
ssh root@YOUR_SERVER
crontab -l | grep update_site.sh
```

Should show:
```
0 */2 * * * cd /home/wiptech/domains/smw.cyring.store/public_python && bash scripts/update_site.sh >> logs/deployment/cron.log 2>&1
```

### Check .env File

```bash
ssh root@YOUR_SERVER
cat /home/wiptech/domains/smw.cyring.store/public_python/.env
```

Should contain:
```
DB_ENGINE=django_tenants.postgresql_backend
DB_NAME=p7152_smw
DB_USER=p7152_smw
DB_PASSWORD=LUGLsxDp7ptf
DB_HOST=pgsql3.serv00.com
```

### Check Script Permissions

```bash
ssh root@YOUR_SERVER
ls -la /home/wiptech/domains/smw.cyring.store/public_python/scripts/update_site.sh
```

Should show executable permission: `-rwxr-xr-x`

### Monitor First Deployment

Cron job runs at:
- Every even hour at 00 minutes (00:00, 02:00, 04:00, etc.)

Check logs:
```bash
ssh root@YOUR_SERVER
tail -f /home/wiptech/domains/smw.cyring.store/public_python/logs/deployment/cron.log
```

## Step 5: Admin Dashboard Access

Once deployed, admins can trigger manual deployments:

1. Visit: `https://smw.pgwiz.cloud/dashboard/deployment/dashboard/`
2. Login with: `admins` / `haha6admin`
3. Click "Trigger Update" to run deployment manually
4. View logs in real-time

## Environment Variables

The script creates `.env` with these variables (customizable via CLI flags):

```bash
DB_ENGINE=django_tenants.postgresql_backend
DB_NAME=p7152_smw
DB_USER=p7152_smw
DB_PASSWORD=LUGLsxDp7ptf
DB_HOST=pgsql3.serv00.com
DB_PORT=5432
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=django-insecure-...
ALLOWED_HOSTS=smw.pgwiz.cloud,smw.cyring.store
SITE_URL=https://smw.pgwiz.cloud
```

## Troubleshooting

### Connection Failed
- Verify hostname/IP is correct
- Check SSH credentials
- Ensure firewall allows SSH (port 22)

### .env Already Exists
- Script will preserve existing .env
- To force recreate, manually delete .env on server first

### Cron Job Already Exists
- Script detects and skips if already present
- To modify, edit directly: `crontab -e`

### Script Not Executable
- Run manually: `bash scripts/update_site.sh`
- Or: `chmod +x scripts/update_site.sh && ./scripts/update_site.sh`

## Deployment Flow

```
Local Machine (deploy.py)
        ↓
SSH Connect to Server
        ↓
Check/Create .env
        ↓
Verify Scripts
        ↓
Create Log Directories
        ↓
Setup Cron Job
        ↓
Test Database Connection
        ↓
Complete ✓
        ↓
Automatic Deployments Every 2 Hours
        ↓
Manual Trigger via Admin Dashboard
```

## Security Notes

- ⚠️ Never commit `deploy.py` with hardcoded credentials (added to .gitignore)
- ⚠️ SSH password prompts in terminal (not saved)
- ⚠️ .env file on server has restricted permissions (600)
- ⚠️ Admin dashboard requires Django staff/superuser login
- ⚠️ Backup files stored in `.backups/` (not committed to git)

## Next Steps

1. Install paramiko: `pip install paramiko`
2. Run deploy script with your server credentials
3. Verify cron job is active
4. Monitor first automatic deployment (2-hour cycle)
5. Test manual trigger from admin dashboard
