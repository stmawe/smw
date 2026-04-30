#!/bin/bash
# UniMarket Platform - Quick Deployment Setup
# Run this to deploy to production server

set -e

echo "=========================================="
echo "UniMarket Platform - Deployment Setup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install Python 3.7+"
    exit 1
fi

# Install paramiko
echo "📦 Installing paramiko..."
pip install paramiko >/dev/null 2>&1 || pip3 install paramiko >/dev/null 2>&1

echo "✓ Paramiko installed"
echo ""

# Prompt for credentials
echo "Enter production server details:"
read -p "Server hostname/IP: " SERVER_HOST
read -p "SSH user (default: root): " SSH_USER
SSH_USER=${SSH_USER:-root}

echo ""
echo "Authentication method:"
echo "1) SSH Password"
echo "2) SSH Key"
read -p "Choose (1 or 2): " AUTH_METHOD

if [ "$AUTH_METHOD" = "1" ]; then
    read -sp "SSH password: " SSH_PASS
    echo ""
    echo ""
    echo "🚀 Running deployment setup..."
    python3 deploy.py \
        --host "$SERVER_HOST" \
        --user "$SSH_USER" \
        --password "$SSH_PASS" \
        --push
elif [ "$AUTH_METHOD" = "2" ]; then
    read -p "SSH key path (default: ~/.ssh/id_rsa): " SSH_KEY
    SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}
    echo ""
    echo "🚀 Running deployment setup..."
    python3 deploy.py \
        --host "$SERVER_HOST" \
        --user "$SSH_USER" \
        --key "$SSH_KEY" \
        --push
else
    echo "❌ Invalid choice"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ Deployment setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify cron: ssh $SSH_USER@$SERVER_HOST 'crontab -l | grep update_site'"
echo "2. Check .env: ssh $SSH_USER@$SERVER_HOST 'cat /home/wiptech/domains/smw.cyring.store/public_python/.env'"
echo "3. Admin dashboard: https://smw.pgwiz.cloud/dashboard/deployment/dashboard/"
echo "4. Login: admins / haha6admin"
echo ""
