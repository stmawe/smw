#!/bin/bash
# SSL Certificate Setup for Serv00 using Devil CLI
# Generates Let's Encrypt wildcard certificate for *.smw.pgwiz.cloud
# Uses Serv00's built-in devil ssl command (proper way for shared hosting)

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== SSL Certificate Setup for Serv00 (Devil CLI) ===${NC}"
echo ""

# Get default IP address
echo -e "${YELLOW}Step 1: Detecting default IP address...${NC}"
DEFAULT_IP=$(devil www list | grep -o "IP: [0-9.]*" | head -1 | awk '{print $2}')

if [ -z "$DEFAULT_IP" ]; then
    echo -e "${RED}ERROR: Could not detect default IP address${NC}"
    echo "Please run: devil www list"
    exit 1
fi

echo -e "${GREEN}✓ Default IP: $DEFAULT_IP${NC}"

# Generate Let's Encrypt certificate for base domain
echo ""
echo -e "${YELLOW}Step 2: Generating Let's Encrypt certificate for smw.pgwiz.cloud...${NC}"
devil ssl www add "$DEFAULT_IP" le le smw.pgwiz.cloud

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Certificate for smw.pgwiz.cloud created${NC}"
else
    echo -e "${RED}ERROR: Failed to create certificate for smw.pgwiz.cloud${NC}"
    exit 1
fi

# Generate Let's Encrypt certificate for wildcard
echo ""
echo -e "${YELLOW}Step 3: Generating Let's Encrypt wildcard certificate for *.smw.pgwiz.cloud...${NC}"
devil ssl www add "$DEFAULT_IP" le le "*.smw.pgwiz.cloud"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Wildcard certificate for *.smw.pgwiz.cloud created${NC}"
else
    echo -e "${RED}ERROR: Failed to create wildcard certificate${NC}"
    exit 1
fi

# List certificates
echo ""
echo -e "${YELLOW}Step 4: SSL Certificate Status${NC}"
devil ssl www list

echo ""
echo -e "${GREEN}=== SSL Setup Complete! ===${NC}"
echo ""
echo "Certificates are now active for:"
echo "  • smw.pgwiz.cloud"
echo "  • *.smw.pgwiz.cloud (includes admin.smw.pgwiz.cloud, all shop subdomains)"
echo ""
echo "Auto-renewal: Enabled by default on Serv00"
echo ""
echo "Test with:"
echo "  curl -I https://smw.pgwiz.cloud"
echo "  curl -I https://admin.smw.pgwiz.cloud"
echo ""
