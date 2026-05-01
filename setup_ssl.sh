#!/bin/bash
# SSL Certificate Setup Script for Serv00
# Issues a wildcard certificate for *.smw.pgwiz.cloud using Cloudflare DNS validation
# 
# Prerequisites:
#   Add CF_API_TOKEN to your .env file on Serv00:
#   CF_API_TOKEN="your_cloudflare_api_token_here"
#
# Usage:
#   source .env  # Load variables from .env
#   bash setup_ssl.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== SSL Certificate Setup for Serv00 ===${NC}"
echo ""

# Try to load .env file if it exists and CF_API_TOKEN is not set
if [ -z "$CF_API_TOKEN" ] && [ -f ".env" ]; then
    echo -e "${YELLOW}Loading CF_API_TOKEN from .env file...${NC}"
    export $(grep CF_API_TOKEN .env | xargs)
fi

# Check if API token is provided
if [ -z "$CF_API_TOKEN" ]; then
    echo -e "${RED}ERROR: CF_API_TOKEN not found${NC}"
    echo ""
    echo "To set up SSL, add CF_API_TOKEN to your .env file on Serv00:"
    echo ""
    echo "  1. SSH into Serv00:"
    echo "     ssh user@serv00.com"
    echo ""
    echo "  2. Edit .env file:"
    echo "     nano .env"
    echo ""
    echo "  3. Add this line (with your actual token):"
    echo "     CF_API_TOKEN=\"your_cloudflare_api_token_here\""
    echo ""
    echo "  4. Save and exit (Ctrl+X, then Y, then Enter)"
    echo ""
    echo "  5. Run this script:"
    echo "     source .env"
    echo "     bash setup_ssl.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Cloudflare API token loaded from .env${NC}"

# Step 1: Install certbot and cloudflare plugin
echo ""
echo -e "${YELLOW}Step 1: Installing Certbot and Cloudflare plugin...${NC}"

# Try venv first (for shared hosting), then global pip
if [ -f "venv/bin/pip" ]; then
    venv/bin/pip install --quiet certbot certbot-dns-cloudflare
    CERTBOT_CMD="venv/bin/certbot"
else
    pip install --quiet certbot certbot-dns-cloudflare
    CERTBOT_CMD="certbot"
fi

echo -e "${GREEN}✓ Installation complete${NC}"

# Step 2: Create secrets directory and credentials file
echo ""
echo -e "${YELLOW}Step 2: Setting up Cloudflare credentials...${NC}"
mkdir -p ~/.secrets

# Create credentials file with API token
cat > ~/.secrets/cf.ini << EOF
# Cloudflare API credentials for DNS-01 challenge
dns_cloudflare_api_token = $CF_API_TOKEN
EOF

# Set strict permissions (600 = rw-------)
chmod 600 ~/.secrets/cf.ini
echo -e "${GREEN}✓ Credentials file created at ~/.secrets/cf.ini with secure permissions (600)${NC}"

# Step 3: Issue wildcard certificate
echo ""
echo -e "${YELLOW}Step 3: Issuing wildcard SSL certificate...${NC}"
echo "This may take a minute while Cloudflare validates DNS..."
echo ""

$CERTBOT_CMD certonly \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cf.ini \
  -d "smw.pgwiz.cloud" \
  -d "*.smw.pgwiz.cloud"

echo ""
echo -e "${GREEN}✓ Certificate issued successfully!${NC}"

# Step 4: Display certificate info
echo ""
echo -e "${YELLOW}Step 4: Certificate Details${NC}"
CERT_DIR="/etc/letsencrypt/live/smw.pgwiz.cloud"

if [ -d "$CERT_DIR" ]; then
    echo -e "${GREEN}Certificate Location:${NC} $CERT_DIR"
    echo ""
    
    # Show expiration date
    if command -v openssl &> /dev/null; then
        echo -e "${GREEN}Certificate Info:${NC}"
        openssl x509 -in "$CERT_DIR/cert.pem" -noout -dates
        echo ""
        openssl x509 -in "$CERT_DIR/cert.pem" -noout -subject
        echo ""
    fi
    
    # Show certificate files
    echo -e "${GREEN}Certificate Files:${NC}"
    echo "  - Private Key: $CERT_DIR/privkey.pem"
    echo "  - Certificate: $CERT_DIR/cert.pem"
    echo "  - Chain: $CERT_DIR/chain.pem"
    echo "  - Full Chain: $CERT_DIR/fullchain.pem"
    echo ""
else
    echo -e "${RED}ERROR: Certificate directory not found at $CERT_DIR${NC}"
    exit 1
fi

# Step 5: Setup auto-renewal
echo ""
echo -e "${YELLOW}Step 5: Setting up auto-renewal...${NC}"

# Use venv certbot if available
if [ -f "venv/bin/certbot" ]; then
    CRON_CERTBOT="venv/bin/certbot"
else
    CRON_CERTBOT="certbot"
fi

CRON_JOB="0 0,12 * * * cd $PWD && $CRON_CERTBOT renew --quiet"
CRON_FILE="/tmp/certbot_cron.txt"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    echo -e "${GREEN}✓ Auto-renewal cron job already configured${NC}"
else
    (crontab -l 2>/dev/null || echo "") | grep -v "^$" > "$CRON_FILE"
    echo "$CRON_JOB" >> "$CRON_FILE"
    crontab "$CRON_FILE"
    rm "$CRON_FILE"
    echo -e "${GREEN}✓ Auto-renewal cron job added${NC}"
    echo "  Renewal check: Daily at 00:00 and 12:00"
fi

# Step 6: Security recommendations
echo ""
echo -e "${YELLOW}Security Notes:${NC}"
echo "  • Keep ~/.secrets/cf.ini private (already set to 600)"
echo "  • Never commit credentials to git"
echo "  • Rotate API token regularly"
echo "  • Certificate renews automatically 30 days before expiry"
echo ""

echo -e "${GREEN}=== SSL Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Configure your web server to use the certificate"
echo "  2. Test with: curl -I https://smw.pgwiz.cloud"
echo "  3. Test wildcard with: curl -I https://admin.smw.pgwiz.cloud"
echo ""
