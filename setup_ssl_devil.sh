#!/bin/bash
# SSL Certificate Setup for Serv00 using Devil CLI
# Automatically adds Let's Encrypt certificates via Serv00's native devil ssl command
# Called by: python deploy.py -ssl
# Also callable from: python deploy.py -dcuf setup_ssl_devil.sh

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Serv00 SSL Certificate Setup (Devil CLI) ===${NC}"
echo ""

# Default IP for Serv00
DEFAULT_IP="128.204.223.70"
echo -e "${GREEN}✓ Using IP: $DEFAULT_IP${NC}"

# Function to add SSL certificate
add_ssl_cert() {
    local domain=$1
    echo ""
    echo -e "${YELLOW}Adding SSL for: $domain${NC}"
    
    result=$(devil ssl www add "$DEFAULT_IP" le le "$domain" 2>&1)
    
    if echo "$result" | grep -q "Certificate added successfully\|already being used"; then
        echo -e "${GREEN}✓ $domain certificate configured${NC}"
        return 0
    else
        echo -e "${YELLOW}~ $domain: $result${NC}"
        return 0
    fi
}

echo ""
echo -e "${YELLOW}Adding certificates...${NC}"

# Add main domain
add_ssl_cert "smw.pgwiz.cloud"

# Add admin subdomain
add_ssl_cert "admin.smw.pgwiz.cloud"

echo ""
echo -e "${YELLOW}Current SSL Certificates:${NC}"
devil ssl www list 2>/dev/null | grep -E "smw.pgwiz.cloud|admin.smw.pgwiz.cloud" || true

echo ""
echo -e "${GREEN}=== SSL Setup Complete ===${NC}"
echo ""
