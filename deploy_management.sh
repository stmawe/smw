#!/bin/bash

# Navigate to the correct directory
cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python

# Create management directory structure
mkdir -p app/management/commands

# Create __init__.py files if they don't exist
touch app/management/__init__.py
touch app/management/commands/__init__.py

echo "Management directory structure created"
pwd
ls -la app/management/commands/
