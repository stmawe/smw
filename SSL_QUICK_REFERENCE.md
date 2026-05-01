# Quick SSL Setup Reference for Serv00

## On Your Local Machine
Nothing needed - keep your API token safe locally.

## On Serv00 (SSH Terminal)

### 1. SSH into Serv00
```bash
ssh your_username@serv00_host.serv00.com
cd ~/path/to/smw
```

### 2. Edit .env file
```bash
nano .env
```

Add this line (with your actual token):
```
CF_API_TOKEN="d75e12eb6631fbb562b3d5d2669326df"
```

Save: `Ctrl+X` → `Y` → `Enter`

### 3. Run SSL Setup
```bash
source .env
bash setup_ssl.sh
```

### 4. That's it! 🎉

The script will:
- ✓ Install Certbot
- ✓ Create credentials file
- ✓ Issue wildcard certificate
- ✓ Set up auto-renewal

---

## Verify Installation

```bash
# Check certificate
certbot certificates

# Test HTTPS
curl -I https://smw.pgwiz.cloud
curl -I https://admin.smw.pgwiz.cloud
```

---

## Emergency: Renew Certificate Now

```bash
source .env
certbot renew --force-renewal
```

---

## Important Notes

✅ **Good:**
- Token in .env on Serv00 only
- .env never committed to git
- Auto-renewal handles it automatically

❌ **Bad:**
- Don't share your API token
- Don't commit .env to git
- Don't hardcode tokens in scripts

---

## File Locations (After Setup)

```
~/.secrets/cf.ini                              # Credentials (600 permissions)
/etc/letsencrypt/live/smw.pgwiz.cloud/        # Certificate files
  ├── privkey.pem                               # Private key
  ├── cert.pem                                  # Certificate
  ├── chain.pem                                 # Chain
  └── fullchain.pem                             # Full chain (for web server)
```

---

## Web Server Config (NGINX Example)

After certificate is issued, update your NGINX config:

```nginx
server {
    listen 443 ssl http2;
    server_name smw.pgwiz.cloud *.smw.pgwiz.cloud;
    
    ssl_certificate /etc/letsencrypt/live/smw.pgwiz.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smw.pgwiz.cloud/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}

server {
    listen 80;
    server_name smw.pgwiz.cloud *.smw.pgwiz.cloud;
    return 301 https://$server_name$request_uri;
}
```

---

## Troubleshooting

### Token not found
```bash
# Check if .env exists
ls -la .env

# Verify token is set
echo $CF_API_TOKEN

# Try again
source .env
bash setup_ssl.sh
```

### DNS validation timeout
```bash
# Wait for DNS propagation, then retry
sleep 60
certbot renew
```

### Check renewal logs
```bash
tail -50 /var/log/letsencrypt/letsencrypt.log
```

---

## Support

Full guide: See `SSL_SETUP_GUIDE.md` in project root
