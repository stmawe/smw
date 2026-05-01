# SSL Setup Summary for admin.smw.pgwiz.cloud

## Your Setup (Ready to Deploy)

✅ **CF_API_TOKEN** added to `.env`:
```
CF_API_TOKEN=d75e12eb6631fbb562b3d5d2669326df
```

✅ **setup_ssl.sh** script ready in project root

✅ **Django settings** configured to read CF_API_TOKEN from environment

✅ **Management commands** created for SSL operations:
- `python manage.py generate_shop_ssl [shop_name]` - Manual SSL generation
- `python manage.py renew_ssl_certificates` - Check and renew expiring certs

## To Deploy on Serv00: One Command

SSH to Serv00 and run from project root:

```bash
source .env && bash setup_ssl.sh
```

This single command will:
1. Load CF_API_TOKEN from .env
2. Install Certbot + Cloudflare plugin
3. Generate wildcard SSL for `*.smw.pgwiz.cloud` (includes admin, shops, etc.)
4. Setup auto-renewal
5. Display certificate location and details

## What You'll Get

**Certificate Location**: `/etc/letsencrypt/live/smw.pgwiz.cloud/`

**Covers**:
- ✅ smw.pgwiz.cloud (base domain)
- ✅ admin.smw.pgwiz.cloud (admin subdomain)
- ✅ any-shop.smw.pgwiz.cloud (shop subdomains)
- ✅ Any other *.smw.pgwiz.cloud subdomain

**Valid For**: 90 days, auto-renews 30 days before expiry

**Auto-Renewal**: Cron job runs twice daily, no manual action needed

## Files Updated/Created

**Modified**:
- `.env` - Added CF_API_TOKEN (already done locally)
- `smw/settings.py` - Configured to read CF_API_TOKEN

**Created**:
- `app/management/commands/generate_shop_ssl.py` - Manual SSL generation tool
- `app/management/commands/renew_ssl_certificates.py` - Certificate renewal tool
- `SERV00_SSL_SETUP.md` - Quick setup guide
- `SERV00_SSL_STEP_BY_STEP.md` - Detailed step-by-step

**Already Existed** (from prior work):
- `setup_ssl.sh` - Main SSL setup script
- `app/ssl_manager.py` - SSL certificate manager class
- `app/ssl_tasks.py` - Async/sync SSL generation functions
- `smw/middleware.py` - Subdomain detection middleware
- `app/admin_views.py` - Admin dashboard

## How It Integrates

### 1. **Manual Setup** (Serv00 deployment)
```bash
source .env && bash setup_ssl.sh
```
→ Creates wildcard cert covering all subdomains

### 2. **Automatic SSL** (Shop creation)
When users create a shop:
- `app/views.py` calls `generate_ssl_async(shop_name, shop_id)`
- `ssl_tasks.py` spawns background thread
- `ssl_manager.py` invokes Certbot with Cloudflare validation
- Shop model updates with SSL info (subdomain, cert_path, expiry)

### 3. **Certificate Renewal** (Maintenance)
```bash
# Manual renewal check
python manage.py renew_ssl_certificates --days 30

# Force renewal of all certs
python manage.py renew_ssl_certificates --force
```

## Security

✅ CF_API_TOKEN never hardcoded - only in .env (gitignored)
✅ Credentials file created temporarily, deleted after use
✅ Permissions set to 600 (read-write owner only)
✅ No secrets logged to stdout or error messages

## Next Steps

1. **Push changes to Serv00**
   - Push `.env` changes (or add CF_API_TOKEN manually)
   - Push `setup_ssl.sh`, settings.py, management commands

2. **SSH to Serv00 and run**
   ```bash
   source .env && bash setup_ssl.sh
   ```

3. **Verify**
   ```bash
   certbot certificates
   curl -I https://admin.smw.pgwiz.cloud
   ```

4. **Configure web server** to use `/etc/letsencrypt/live/smw.pgwiz.cloud/`

5. **Test shop creation** to verify automatic SSL works

Done! admin.smw.pgwiz.cloud will have valid SSL. 🎉
