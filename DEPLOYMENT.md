# UniMarket Platform - Deployment & Site Update System

## Overview

This documentation describes the comprehensive site update and deployment system for the UniMarket platform running at `smw.pgwiz.cloud`.

## Components

### 1. Update Script (`scripts/update_site.sh`)

**Location:** `/home/wiptech/domains/smw.cyring.store/public_python/scripts/update_site.sh`

**Purpose:** Comprehensive deployment automation that:
- Fetches latest code from Git
- Manages virtual environment
- Protects sensitive files (.env, db.sqlite3, etc.)
- Backs up protected files before deployment
- Runs Django migrations
- Collects and compresses static files
- Reloads web services

**Features:**
- **File Protection:** Automatically backs up .env and other sensitive files
- **Lock Management:** Prevents concurrent deployments
- **Error Handling:** Graceful failure with detailed logging
- **Service Reloading:** Supports DevilWebPanel, Gunicorn, and uWSGI
- **Backup System:** Maintains timestamped backups of critical files

**Cron Job:**
The script runs automatically every 2 hours:
```bash
0 */2 * * * cd /home/wiptech/domains/smw.cyring.store/public_python && bash scripts/update_site.sh
```

### 2. Admin Deployment Dashboard

**URL:** `/dashboard/deployment/dashboard/`

**Access:** Only available to users with staff/superuser privileges

**Features:**
- One-click site update trigger
- Real-time deployment log viewing
- Recent deployment history
- Update status monitoring

**Default Admin Credentials:**
```
Username: admins
Password: haha6admin
```

### 3. Django Management Commands

#### Seed Admin Users
```bash
python manage.py seed_admins
```

Creates or updates the default admin user with staff privileges.

## Protected Files

The following files are automatically backed up before each deployment:
- `.env` - Environment configuration
- `.env.production` - Production environment variables
- `db.sqlite3` - SQLite database (if used)
- `config/secrets.py` - Secret configuration

**Backup Location:** `.backups/` directory with timestamp in filename

Example backup files:
```
.backups/.env.1617283200.backup
.backups/.env.production.1617283201.backup
```

## Security Considerations

### 1. .env File Protection

**NEVER commit .env to Git:**
```bash
# Ensure .gitignore contains:
echo ".env" >> .gitignore
echo ".env.production" >> .gitignore
echo "db.sqlite3" >> .gitignore
```

**Backup your .env:**
The update script automatically backs up .env before pulling changes. If an update fails, the backup is restored.

### 2. Admin Dashboard Access

- Only accessible to authenticated staff users (is_staff=True)
- Requires admin group membership or superuser status
- CSRF protection on all update actions

### 3. Cron Job Security

The cron job runs as the web server user:
- No direct web access can trigger updates (must use admin dashboard)
- Update logs stored in `/logs/update/` directory
- Each update logged with timestamp and user info

## Deployment Workflow

### Manual Deployment (via Admin Dashboard)

1. Log in with admin credentials
2. Navigate to `/dashboard/deployment/dashboard/`
3. Click "Trigger Site Update" button
4. Monitor logs in real-time
5. Update completes in background

### Automated Deployment (Cron Job)

1. Script runs every 2 hours automatically
2. Fetches latest changes from `origin main` branch
3. Backs up protected files
4. Runs migrations
5. Collects static files
6. Reloads services
7. Logs output to timestamped log file

### Deployment Steps

The update script performs these steps in order:

```
1. Check for concurrent deployments (lock)
2. Navigate to repository directory
3. Activate virtual environment
4. Back up protected files
5. Git stash local changes
6. Git fetch from origin
7. Git pull origin main
8. Restore protected files
9. Git stash apply (reapply local changes)
10. Check for dependency changes in requirements.txt
11. Install dependencies if changed
12. Run Django checks
13. Run Django migrations
14. Collect static files
15. Compress static files (optional)
16. Clear cache (optional)
17. Reload web services (DevilWebPanel, Gunicorn, uWSGI)
```

## Logging

### Log Location
- **Update logs:** `/home/wiptech/domains/smw.cyring.store/logs/update/`
- **Log format:** `deploy-YYYY-MM-DD-HH-MM-SS.log`

### Log Contents
Each log file contains:
- Timestamp of deployment
- User who triggered update (if manual)
- User IP address (if manual)
- All Git operations
- All Django management commands
- All errors and warnings
- Final status

### Viewing Logs

**Via Admin Dashboard:**
1. Go to `/dashboard/deployment/dashboard/`
2. Scroll to "Recent Deployment Logs" section
3. Click on any log file to view

**Via Command Line:**
```bash
# View most recent log
tail -f /home/wiptech/domains/smw.cyring.store/logs/update/deploy-*.log

# View specific log
cat /home/wiptech/domains/smw.cyring.store/logs/update/deploy-2024-04-30-14-00.log
```

## Troubleshooting

### Update Fails to Start

**Symptom:** "Update script not found" error

**Solution:**
1. Ensure `scripts/update_site.sh` exists
2. Check file permissions: `chmod +x scripts/update_site.sh`
3. Verify path is correct in deployment_views.py

### Concurrent Deployment Error

**Symptom:** "Update already in progress" error

**Solution:**
1. Check if another deployment is running: `ps aux | grep update_site.sh`
2. If stale process: `kill <PID>` and `rm /tmp/smw-update.pid`
3. Try deployment again

### Protected Files Not Restored

**Symptom:** .env or other files missing after deployment

**Solution:**
1. Check backup directory: `ls -la .backups/`
2. Manually restore from backup: `cp .backups/.env.*.backup .env`
3. Check file permissions

### Services Not Reloading

**Symptom:** Changes not visible after deployment

**Possible Causes:**
- DevilWebPanel not installed
- Gunicorn/uWSGI process not running
- Incorrect permissions

**Solution:**
1. Check which service is running: `ps aux | grep -E "(gunicorn|uwsgi|devil)"`
2. Verify log output in deployment logs
3. Manually restart service if needed

## Configuration

### Environment Variables

Create `.env` file in repository root:
```bash
# Database
DB_ENGINE=django_tenants.postgresql_backend
DB_NAME=smw
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django
DEBUG=False
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=smw.pgwiz.cloud,smw.cyring.store

# Deployment paths (update in update_site.sh if different)
REPO_DIR=/home/wiptech/domains/smw.cyring.store/public_python/
```

### Update Script Configuration

Edit `scripts/update_site.sh` to customize:
- Repository path: `REPO_DIR`
- Virtual environment: `VENV_DIR`
- Log directory: `LOG_DIR`
- Service restart method
- Protected files list

## Maintenance

### Clean Up Old Backups

```bash
# Keep only last 10 backups
cd /home/wiptech/domains/smw.cyring.store/public_python/.backups/
ls -t | tail -n +11 | xargs rm -f
```

### Clean Up Old Logs

```bash
# Keep only last 30 days of logs
find /home/wiptech/domains/smw.cyring.store/logs/update/ -type f -mtime +30 -delete
```

### Verify Deployment Health

```bash
# Check last deployment log
tail -20 /home/wiptech/domains/smw.cyring.store/logs/update/deploy-*.log | head -1

# Check if services are running
ps aux | grep -E "(gunicorn|uwsgi|python manage.py)"

# Check disk space
df -h /home/wiptech/domains/

# Check backup integrity
ls -lh /home/wiptech/domains/smw.cyring.store/public_python/.backups/
```

## Best Practices

1. **Never manually edit .env** - Use deployment dashboard for configuration changes
2. **Review logs regularly** - Check deployment logs for issues
3. **Test in staging** - Deploy to staging before production
4. **Keep backups** - Maintain off-site backups of critical files
5. **Monitor disk space** - Ensure adequate space for backups and logs
6. **Document changes** - Commit meaningful messages to Git
7. **Use admin dashboard** - Prefer admin dashboard over SSH/cron for updates

## Emergency Procedures

### Rollback Failed Deployment

```bash
# Stop the failed deployment (if still running)
pkill -f update_site.sh

# Restore from backup
cp .backups/.env.*.backup .env
git reset --hard HEAD~1

# Manually restart services
devil www restart smw.cyring.store
```

### Manual Deployment Without Script

```bash
cd /home/wiptech/domains/smw.cyring.store/public_python/
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate_schemas
python manage.py collectstatic --noinput
devil www restart smw.cyring.store
```

### Restore from Old Backup

```bash
# Find the backup you need
ls -lah .backups/

# Restore specific file
cp .backups/.env.1617283200.backup .env

# Restore all files from specific timestamp
cp .backups/.env.*.1617283200.backup .env
cp .backups/.env.production.*.1617283200.backup .env.production
```

## Support

For issues or questions:
1. Check logs: `/logs/update/deploy-*.log`
2. Review this documentation
3. Contact DevOps team
4. Check GitHub repository for recent changes

---

**Last Updated:** 2024-04-30
**Version:** 1.0
**Maintainer:** DevOps Team
