# Step-by-Step SSL Setup for admin.smw.pgwiz.cloud

## Complete Instructions for Serv00

### Step 1: SSH into Serv00
```bash
ssh pgwiz@serv00.com
```

### Step 2: Navigate to Project Directory
```bash
cd /path/to/smw  # (wherever your Django project is)
```

### Step 3: Verify .env File Has Token
```bash
# Check if CF_API_TOKEN is in .env
cat .env | grep CF_API_TOKEN

# Expected output:
# CF_API_TOKEN=d75e12eb6631fbb562b3d5d2669326df
```

If not present, add it:
```bash
nano .env
# Add this line:
# CF_API_TOKEN=d75e12eb6631fbb562b3d5d2669326df
# Save: Ctrl+X → Y → Enter
```

### Step 4: Load Environment Variables
```bash
source .env
```

Verify loaded:
```bash
echo $CF_API_TOKEN
# Should print: d75e12eb6631fbb562b3d5d2669326df
```

### Step 5: Run SSL Setup Script
```bash
bash setup_ssl.sh
```

The script will:
- 📦 Install Certbot and Cloudflare plugin
- 🔑 Create credentials file at ~/.secrets/cf.ini
- 📜 Generate wildcard certificate for *.smw.pgwiz.cloud (includes admin.smw.pgwiz.cloud)
- ⏰ Setup automatic renewal
- ✅ Display certificate location and details

### Step 6: Verify Certificate Was Created
```bash
# List all certificates
certbot certificates

# Expected output should show:
# Certificate Name: smw.pgwiz.cloud
# Domains: smw.pgwiz.cloud, *.smw.pgwiz.cloud
# Path: /etc/letsencrypt/live/smw.pgwiz.cloud
```

### Step 7: View Certificate Files
```bash
ls -la /etc/letsencrypt/live/smw.pgwiz.cloud/

# Should show:
# cert.pem        → The SSL certificate
# privkey.pem     → The private key
# chain.pem       → CA chain
# fullchain.pem   → Full certificate chain
```

### Step 8: Configure Web Server

**For Phusion Passenger (Serv00 control panel):**
1. Go to domain settings
2. Add SSL certificate
3. Point to: `/etc/letsencrypt/live/smw.pgwiz.cloud/cert.pem`
4. Point private key to: `/etc/letsencrypt/live/smw.pgwiz.cloud/privkey.pem`
5. Save

Or manually in Nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name smw.pgwiz.cloud *.smw.pgwiz.cloud;
    
    ssl_certificate /etc/letsencrypt/live/smw.pgwiz.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smw.pgwiz.cloud/privkey.pem;
    
    # ... rest of config
}
```

### Step 9: Test the Certificate

```bash
# Test main domain
curl -I https://smw.pgwiz.cloud

# Test admin subdomain  
curl -I https://admin.smw.pgwiz.cloud

# Both should return: HTTP/1.1 200 OK or 301 redirect
```

### Step 10: Verify Auto-Renewal is Set

```bash
# View cron jobs
crontab -l

# Should include:
# 0 0,12 * * * certbot renew --quiet
```

## What Happens Now

✅ **Certificate Created**: Wildcard cert for `*.smw.pgwiz.cloud`  
✅ **Covers Subdomains**: `admin.smw.pgwiz.cloud`, any `shopname.smw.pgwiz.cloud`  
✅ **Auto-Renewal**: Certbot checks daily, renews 30 days before expiry  
✅ **Secure**: Token stored only in `.env`, never in git  

## Certificate Expiration

The certificate is valid for **90 days** from issue date.

Check when it expires:
```bash
openssl x509 -in /etc/letsencrypt/live/smw.pgwiz.cloud/cert.pem -noout -dates
```

Certbot automatically renews it 30 days before expiry (no action needed).

## Troubleshooting

### Issue: "CF_API_TOKEN not found"
```bash
# Solution: Make sure to source .env before running
source .env
echo $CF_API_TOKEN  # Should show the token
bash setup_ssl.sh
```

### Issue: "certbot: command not found"
```bash
# Solution: Install certbot manually
pip install certbot certbot-dns-cloudflare
bash setup_ssl.sh
```

### Issue: "DNS validation failed"
```bash
# Solution: Check Cloudflare API token is valid
# 1. Go to https://dash.cloudflare.com/profile/api-tokens
# 2. Create new token with DNS:Edit permission
# 3. Update .env with new token
# 4. Try again: source .env && bash setup_ssl.sh
```

### Issue: "Permission denied"
```bash
# Solution: Run with sudo
sudo bash setup_ssl.sh
# Note: Still need to source .env first for CF_API_TOKEN
source .env
sudo bash setup_ssl.sh
```

## Next Steps

After SSL is set up:
1. ✅ Configure web server to use certificates
2. ✅ Test https://admin.smw.pgwiz.cloud loads without errors
3. ✅ Create shops and verify SSL works for shop subdomains
4. ✅ Monitor certificate renewal (check logs after 30 days)

Done! 🎉
