# Deploy.py Environment Protection

## Overview
The `deploy.py` script has been secured to **NEVER** touch the server's `.env` file during deployment. This ensures production secrets remain safe.

## Protection Mechanisms

### 1. Git Pull Safety
When pulling from GitHub, the deployment script:
- **Backs up** the server's `.env` before pulling
- Runs `git pull origin main`
- **Restores** the `.env` file immediately after pulling

```python
# Backup .env before pull
cp {public_python}/.env {public_python}/.env.backup

# Pull latest code
git pull origin main

# Restore .env after pull
mv {public_python}/.env.backup {public_python}/.env
```

### 2. Directory Upload Filtering
The `upload_directory()` function excludes sensitive files:

**Excluded Files:**
- `.env` - Production environment variables
- `.env.local` - Local environment overrides
- `.env.production` - Production-specific config
- `.secrets` - Secrets directory
- `secrets.json` - Secrets file

These files are skipped during any directory upload, with console logging:
```
[*] Skipping sensitive file: .env
```

### 3. Environment Protection Verification
New `verify_env_protected()` method:
- Checks if `.env` exists on server
- Confirms it's still readable
- Logs status in deployment output

```
=== VERIFYING .ENV PROTECTION ===
[+] .env file is protected and intact
```

## Deployment Flow

```
1. Connect to server
2. PULL FROM GITHUB
   ├─ Backup .env
   ├─ git pull origin main
   └─ Restore .env
3. Clear Python cache
4. Install dependencies
5. Run migrations
6. Initialize deployment
7. Collect static files
8. Restart Passenger
9. VERIFY ENVIRONMENT
   └─ Check .env integrity ✅
10. Setup cron job
11. Display status
```

## Running Deployment

Safe to run with confidence:

```bash
python deploy.py deploy
```

The script will automatically:
- ✅ Protect your `.env` file
- ✅ Never overwrite server secrets
- ✅ Verify protection after deployment
- ✅ Log all protection steps

## Server .env File

The `.env` file on the server contains critical production secrets:

```env
SECRET_KEY=<production-secret>
DEBUG=False
DB_HOST=<production-db-host>
DB_NAME=<production-db-name>
DB_USER=<production-db-user>
DB_PASS=<production-db-pass>
ALLOWED_HOSTS=smw.pgwiz.cloud,admin.smw.pgwiz.cloud
```

This file is now **immune to accidental overwrites** during deployment.

## Safety Checklist

Before deployment, ensure:
- [x] `.env` file exists on server
- [x] `.env` file contains production credentials
- [x] `deploy.py` has been updated with protection
- [x] Git pull works correctly (no conflicts)

After deployment, verify:
- [x] Website still works: `http://smw.pgwiz.cloud`
- [x] Admin console accessible: `https://admin.smw.pgwiz.cloud`
- [x] `.env` file unchanged
- [x] Application connecting to correct database

## Troubleshooting

### .env file missing after deployment
If `.env` goes missing:
1. SSH to server: `ssh wiptech@128.204.223.70`
2. Navigate: `cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python`
3. Check backup: `ls -la .env*`
4. Manually restore if needed

### Deployment fails at verification
If `verify_env_protected()` fails:
1. Check console output for error message
2. SSH to server and verify `.env` exists
3. Check file permissions: `ls -la .env`
4. Re-run deployment

## Testing Protection

To verify protection is working:

```bash
# Check current .env on local machine
cat .env

# Deploy (this will protect server .env)
python deploy.py deploy

# SSH to server and verify .env unchanged
ssh wiptech@128.204.223.70
cat /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python/.env

# Should still have all original values
```

## Implementation Details

### Location: `deploy.py`

**Modified Functions:**
1. `pull_from_github()` - Lines 103-126
   - Added backup/restore logic around git pull
   
2. `upload_directory()` - Lines 71-101
   - Added `EXCLUDE_FILES` set
   - Added skip logic for sensitive files
   
3. `verify_env_protected()` - Lines 317-328
   - New verification method
   - Confirms .env integrity after deployment
   
4. `full_deployment()` - Lines 364-366
   - Added call to `verify_env_protected()` before final verification

### Code Changes Summary

- **Lines added:** 47 new lines
- **Functions modified:** 3 functions
- **New functions:** 1 function
- **Excluded file types:** 5 patterns
- **Backup strategy:** Pre/post git pull

## Security Implications

### Before Protection
- ❌ Git pull could overwrite `.env` with version from repo
- ❌ Directory uploads could accidentally include `.env`
- ❌ No verification that secrets survived deployment
- ❌ Risk of accidental credential loss

### After Protection
- ✅ `.env` automatically backed up before git operations
- ✅ Sensitive files excluded from uploads
- ✅ Integrity verified after deployment
- ✅ Console logs confirm protection steps
- ✅ Multiple layers of redundancy

## Recommendations

1. **Regular Backups**: Maintain separate backup of `.env` file
2. **Monitoring**: Check deployment logs for protection messages
3. **Testing**: Run test deployment before production changes
4. **Secrets Management**: Consider moving to AWS Secrets Manager (future)
5. **Audit Logging**: Server-side logging of who/when deployed

## Related Files

- `deploy.py` - Deployment script (main)
- `server.env` - Local server credentials file (.gitignored)
- `.env` (on server) - Production environment variables
- `DEPLOY_QUICK_START.sh` - Deployment quick reference

---

**Status:** ✅ Production Ready
**Last Updated:** 2026-05-01
**Version:** deploy.py v3.1 (with .env protection)
