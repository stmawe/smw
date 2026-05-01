#!/bin/bash
# Test admin login

echo "Testing admin login on https://admin.smw.pgwiz.cloud"
echo "==========================================="

# Step 1: Get the login page and extract CSRF token
echo "Step 1: Getting login page and CSRF token..."
CSRF_TOKEN=$(curl -s -c /tmp/cookies.txt https://admin.smw.pgwiz.cloud/ | grep -oP 'csrfmiddlewaretoken" value="\K[^"]+' | head -1)

if [ -z "$CSRF_TOKEN" ]; then
    echo "✗ Could not extract CSRF token"
    exit 1
fi

echo "✓ CSRF Token: ${CSRF_TOKEN:0:20}..."

# Step 2: Attempt login with username
echo ""
echo "Step 2: Attempting login with username 'admins'..."
RESPONSE=$(curl -s -b /tmp/cookies.txt -c /tmp/cookies2.txt \
    -X POST https://admin.smw.pgwiz.cloud/login/ \
    -d "username=admins&password=haha6admin&csrfmiddlewaretoken=$CSRF_TOKEN" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -i)

STATUS_CODE=$(echo "$RESPONSE" | head -1 | grep -oP '\d{3}')
echo "Response Status: $STATUS_CODE"

if [ "$STATUS_CODE" == "302" ]; then
    echo "✓ Login successful (302 redirect)"
    # Check if we got a session
    curl -s -b /tmp/cookies2.txt https://admin.smw.pgwiz.cloud/dashboard/ | head -3
elif [ "$STATUS_CODE" == "200" ]; then
    echo "✓ Login page returned (may have redirected back)"
    echo "$RESPONSE" | grep -E "Invalid username|Dashboard|Admin" | head -1
else
    echo "✗ Unexpected status code: $STATUS_CODE"
    echo "$RESPONSE" | tail -5
fi

# Step 3: Test with email
echo ""
echo "Step 3: Attempting login with email 'admin@smw.pgwiz.cloud'..."
RESPONSE2=$(curl -s -b /tmp/cookies.txt -c /tmp/cookies3.txt \
    -X POST https://admin.smw.pgwiz.cloud/login/ \
    -d "username=admin@smw.pgwiz.cloud&password=haha6admin&csrfmiddlewaretoken=$CSRF_TOKEN" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -i)

STATUS_CODE2=$(echo "$RESPONSE2" | head -1 | grep -oP '\d{3}')
echo "Response Status: $STATUS_CODE2"

if [ "$STATUS_CODE2" == "302" ]; then
    echo "✓ Email login successful (302 redirect)"
elif [ "$STATUS_CODE2" == "200" ]; then
    echo "✓ Email login page returned"
    echo "$RESPONSE2" | grep -E "Invalid username|Dashboard" | head -1
else
    echo "✗ Unexpected status code: $STATUS_CODE2"
fi

echo ""
echo "Test complete!"
