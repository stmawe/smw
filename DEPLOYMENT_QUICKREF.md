# Deployment System - Quick Reference

## Admin Dashboard Access

**URL:** `https://smw.pgwiz.cloud/dashboard/deployment/dashboard/`

**Credentials:**
- Username: `admins`
- Password: `haha6admin`

**What You Can Do:**
- ✅ Click "Start Update" to deploy latest changes
- ✅ View recent deployment logs
- ✅ Monitor update status in real-time
- ✅ Check if update script is available

## File Locations (On Production Server)

```
Repository: /home/wiptech/domains/smw.cyring.store/public_python/
Update Script: scripts/update_site.sh
Logs: /home/wiptech/domains/smw.cyring.store/logs/update/
Backups: /home/wiptech/domains/smw.cyring.store/public_python/.backups/
```

## Automatic Deployment

**Frequency:** Every 2 hours
**Trigger:** Cron job
**What it does:** Git pull → Migrations → Static files → Service reload

## Manual Deployment

1. Visit `/dashboard/deployment/dashboard/`
2. Click "Start Update"
3. Monitor logs below
4. Update runs in background - page doesn't freeze

## Management Commands

```bash
# Seed admin users
python manage.py seed_admins

# Check system health
python manage.py check

# View migrations
python manage.py showmigrations mydak
```

## Viewing Logs

**Via Dashboard:** `/dashboard/deployment/dashboard/` → Scroll to "Recent Deployment Logs"

**Via SSH:** `tail -f /home/wiptech/domains/smw.cyring.store/logs/update/deploy-*.log`

## Protected Files

These files are automatically backed up before each deployment:
- `.env` - Environment configuration
- `.env.production` - Production settings
- `db.sqlite3` - Database
- `config/secrets.py` - Secrets

**Backup Location:** `.backups/` directory (timestamped)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Update Script Missing" | Run `chmod +x scripts/update_site.sh` on server |
| "Permission Denied" | Log in with admins credentials, verify staff status |
| Update stuck | Check if another update is running, wait or manually kill |
| .env missing after update | Check `.backups/` for backup, restore manually if needed |

## Emergency Rollback

```bash
# Stop current deployment (if running)
pkill -f update_site.sh

# Restore .env from backup
cp .backups/.env.*.backup .env

# Reset to previous Git state
git reset --hard HEAD~1

# Restart services
devil www restart smw.cyring.store
```

## Important Notes

⚠️ **NEVER commit .env to Git** - It's protected by .gitignore

⚠️ **Backups are local** - Keep off-site backups separately

⚠️ **Script runs as web user** - Use admin dashboard instead of SSH

⚠️ **Concurrent updates blocked** - Only one update can run at a time

## Key Features

✅ Automatic backup of sensitive files
✅ Protected .env during deployments  
✅ Real-time deployment monitoring
✅ Admin-only access control
✅ Comprehensive logging
✅ Rollback capability
✅ Prevents concurrent deployments
✅ Auto service reload

---

For detailed information, see `DEPLOYMENT.md` or `DEPLOYMENT_IMPLEMENTATION.md`
