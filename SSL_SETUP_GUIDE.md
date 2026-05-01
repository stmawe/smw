# SSL Certificate Setup Guide for Serv00

## Overview
This guide sets up a wildcard SSL certificate for `*.smw.pgwiz.cloud` using Certbot with Cloudflare DNS validation.

## Prerequisites
- SSH access to Serv00
- Cloudflare account with API token
- Domain `smw.pgwiz.cloud` configured in Cloudflare
- Python/pip installed on Serv00
- `.env` file in your project directory

## Security: API Token Handling (Using .env)

### ✅ SECURE APPROACH: Environment Variables in .env

Your Cloudflare API token should be stored in the `.env` file on Serv00 only:

```bash
# In ~/.env or /path/to/project/.env on Serv00
CF_API_TOKEN="d75e12eb6631fbb562b3d5d2669326df"
```

**Key Security Points:**
- ✅ Token stored in `.env` file (which is in `.gitignore`)
- ✅ Never committed to git repository
- ✅ Only exists on Serv00, not in local development
- ✅ Automatically loaded when running the setup script
- ✅ Not exposed in shell history

### ❌ What NOT to Do:
- Don't hardcode tokens in scripts
- Don't share tokens in messages/emails
- Don't commit `.env` to git
- Don't store in shell rc files (.bashrc, .zshrc)
- Don't pass tokens via command line arguments

## Step-by-Step Instructions

### Step 1: Connect to Serv00 via SSH

```bash
ssh your_username@your_serv00_host.serv00.com
```

### Step 2: Navigate to Project Directory

```bash
cd ~/path/to/smw
```

### Step 3: Add Cloudflare Token to .env

If you don't have a `.env` file, create one:

```bash
nano .env
```

Add or update the line with your Cloudflare API token:

```ini
# Existing variables...
SECRET_KEY=your_existing_secret_key

# Add this line:
CF_API_TOKEN="d75e12eb6631fbb562b3d5d2669326df"
```

Save and exit:
- Press `Ctrl+X`
- Press `Y` (for yes)
- Press `Enter`

### Step 4: Load .env and Run Setup Script

```bash
# Load environment variables from .env
source .env

# Verify token is loaded
echo $CF_API_TOKEN  # Should show your token

# Run the SSL setup script
bash setup_ssl.sh
```

The script will:
1. ✓ Load your API token from .env
2. ✓ Install Certbot and Cloudflare plugin
3. ✓ Create `~/.secrets/cf.ini` with your credentials
4. ✓ Issue wildcard certificate via Cloudflare DNS validation
5. ✓ Display certificate details
6. ✓ Configure auto-renewal cron job

### Step 5: Verify Certificate

```bash
# Check certificate details
certbot certificates

# View full certificate info
openssl x509 -in /etc/letsencrypt/live/smw.pgwiz.cloud/cert.pem -noout -text
```

## Certificate File Locations

After successful setup, certificates are stored at:

```
/etc/letsencrypt/live/smw.pgwiz.cloud/
├── privkey.pem          # Private key (keep secret!)
├── cert.pem             # Certificate only
├── chain.pem            # Intermediate certificates
└── fullchain.pem        # cert.pem + chain.pem (for NGINX/Apache)
```

## Web Server Configuration

### For NGINX

```nginx
server {
    listen 443 ssl http2;
    server_name smw.pgwiz.cloud *.smw.pgwiz.cloud;
    
    ssl_certificate /etc/letsencrypt/live/smw.pgwiz.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smw.pgwiz.cloud/privkey.pem;
    
    # Strong SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name smw.pgwiz.cloud *.smw.pgwiz.cloud;
    return 301 https://$server_name$request_uri;
}
```

### For Apache

```apache
<VirtualHost *:443>
    ServerName smw.pgwiz.cloud
    ServerAlias *.smw.pgwiz.cloud
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/smw.pgwiz.cloud/cert.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/smw.pgwiz.cloud/privkey.pem
    SSLCertificateChainFile /etc/letsencrypt/live/smw.pgwiz.cloud/chain.pem
</VirtualHost>

<VirtualHost *:80>
    ServerName smw.pgwiz.cloud
    ServerAlias *.smw.pgwiz.cloud
    Redirect permanent / https://smw.pgwiz.cloud/
</VirtualHost>
```

## Auto-Renewal

Certbot automatically configures renewal checks via cron.

### Check renewal status

```bash
certbot renew --dry-run
```

### View cron job

```bash
crontab -l | grep certbot
```

### Manual renewal

```bash
certbot renew --force-renewal
```

## Troubleshooting

### Error: "API token invalid or expired"

```bash
# Verify your API token is correct
export CF_API_TOKEN="your_token_here"
bash setup_ssl.sh
```

### Error: "Domain not found in Cloudflare"

```bash
# Ensure:
# 1. Domain smw.pgwiz.cloud is added to Cloudflare
# 2. Nameservers point to Cloudflare
# 3. API token has DNS:edit permissions
```

### Error: "DNS validation timeout"

```bash
# Wait a few seconds for DNS propagation:
sleep 30
certbot renew
```

### Check certificate renewal logs

```bash
# View renewal attempt history
cat /var/log/letsencrypt/letsencrypt.log | tail -50
```

## Updating Cloudflare API Token

If you need to rotate your API token:

```bash
# 1. Create new token in Cloudflare dashboard
# 2. Update the credentials file
export CF_API_TOKEN="new_token_here"
cat > ~/.secrets/cf.ini << EOF
dns_cloudflare_api_token = $CF_API_TOKEN
EOF
chmod 600 ~/.secrets/cf.ini

# 3. Renew certificate
certbot renew --force-renewal
```

## Security Best Practices

### ✅ DO:
- Use environment variables for tokens
- Set credentials file permissions to 600
- Rotate API tokens regularly
- Keep Certbot updated
- Enable HSTS headers (only after SSL is stable)

### ❌ DON'T:
- Commit credentials to git
- Share API tokens in messages/emails
- Use the same token for multiple services
- Store tokens in shell rc files (.bashrc, .zshrc)
- Disable SSL verification

## HSTS Header (After SSL is Working)

Once SSL is confirmed working on all subdomains, add HSTS:

### NGINX
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Apache
```apache
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
```

## Testing

### Test main domain
```bash
curl -I https://smw.pgwiz.cloud
# Should return: HTTP/2 200
```

### Test wildcard subdomain
```bash
curl -I https://admin.smw.pgwiz.cloud
# Should return: HTTP/2 200

curl -I https://my-shop.smw.pgwiz.cloud
# Should return: HTTP/2 200
```

### Check certificate validity
```bash
# Browser: Visit https://smw.pgwiz.cloud - should show 🔒 lock icon
# Verify certificate serves all subdomains
# Check expiration date (should be ~90 days)
```

## Monitoring Certificate Expiration

### Check days until expiration
```bash
echo "Certificate expires in:"
certbot certificates | grep "Expiration Date"
```

### Set calendar reminder (Optional)
```bash
# Set reminder 30 days before expiration (Certbot auto-renews at 30 days)
# If renewal fails, you'll have time to investigate
```

## Additional Resources

- Certbot Documentation: https://certbot.eff.org/docs/
- Cloudflare API: https://api.cloudflare.com/
- Let's Encrypt: https://letsencrypt.org/
- NGINX SSL Configuration: https://nginx.org/en/docs/http/ngx_http_ssl_module.html

## Quick Reference

```bash
# View all certificates
certbot certificates

# Manually test renewal
certbot renew --dry-run

# Update Cloudflare credentials
export CF_API_TOKEN="new_token"
cat > ~/.secrets/cf.ini << EOF
dns_cloudflare_api_token = $CF_API_TOKEN
EOF
chmod 600 ~/.secrets/cf.ini

# Renew now
certbot renew

# Remove certificate
certbot delete --cert-name smw.pgwiz.cloud
```

## Support

If you encounter issues:

1. Check logs: `cat /var/log/letsencrypt/letsencrypt.log`
2. Verify Cloudflare settings in dashboard
3. Test DNS: `dig smw.pgwiz.cloud`
4. Check firewall: `sudo ufw status` (if using UFW)
5. Review web server configuration
