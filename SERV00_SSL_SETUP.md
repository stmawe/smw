# Manual SSL Setup for admin.smw.pgwiz.cloud on Serv00

## Quick Setup (One Command)

SSH into Serv00 and run this from your project root:

```bash
# Load environment and run SSL setup
source .env && bash setup_ssl.sh
```

This will:
1. ✅ Load the Cloudflare API token from `.env`
2. ✅ Install Certbot and Cloudflare plugin
3. ✅ Generate a wildcard SSL certificate for `*.smw.pgwiz.cloud`
4. ✅ Set up automatic renewal via cron job

## What Gets Created

The script will create certificates at:
```
/etc/letsencrypt/live/smw.pgwiz.cloud/
  ├── cert.pem          (certificate)
  ├── privkey.pem       (private key)
  ├── chain.pem         (intermediate certs)
  └── fullchain.pem     (full chain)
```

These certificates will work for:
- `smw.pgwiz.cloud` (base domain)
- `*.smw.pgwiz.cloud` (all subdomains including `admin`, shop names, etc.)

## Verify Certificate

After setup completes, verify it worked:

```bash
# Check certificate details
certbot certificates

# Test admin subdomain
curl -I https://admin.smw.pgwiz.cloud

# View expiration date
openssl x509 -in /etc/letsencrypt/live/smw.pgwiz.cloud/cert.pem -noout -dates
```

## Web Server Configuration

After certificates are created, configure Passenger/Nginx to use them.

For **Phusion Passenger** (Serv00):
1. Go to your control panel
2. Add SSL certificate pointing to `/etc/letsencrypt/live/smw.pgwiz.cloud/`
3. Or update your Nginx config to point to the certificate files

## Automatic Renewal

The script adds a cron job that checks for renewal twice daily (00:00 and 12:00).
Certificates renew automatically 30 days before expiry.

Verify cron is set:
```bash
crontab -l | grep certbot
```

## Troubleshooting

**"CF_API_TOKEN not found"** 
→ Check `.env` file has: `CF_API_TOKEN=d75e12eb6631fbb562b3d5d2669326df`
→ Run: `source .env` before running the script

**"certbot: command not found"**
→ Script installs it, but you may need Python pip
→ Try: `pip install certbot certbot-dns-cloudflare`

**DNS validation fails**
→ Check Cloudflare API token is valid
→ Verify domain is using Cloudflare nameservers
→ Wait a few minutes and retry

**Permission denied on /etc/letsencrypt**
→ Certbot requires sudo or root
→ Run: `sudo bash setup_ssl.sh` (after sourcing .env)

## Environment Variable

The CF_API_TOKEN in `.env`:
```
CF_API_TOKEN=d75e12eb6631fbb562b3d5d2669326df
```

✅ Already added to `.env` on local repo
✅ Make sure it's on Serv00's `.env` before running script
✅ Never commit this to git (it's in `.gitignore`)
