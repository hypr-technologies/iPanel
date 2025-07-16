#!/bin/bash

# iPanel Installation Fix Script
# This script addresses the common installation issues found in the error logs

echo "=== iPanel Installation Fix Script ==="
echo "Fixing dependencies and configuration issues..."

# 1. Install missing system dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    apt-get update
    apt-get install -y openssl libssl-dev libffi-dev python3-dev build-essential pkg-config
    apt-get install -y python3-pip python3-venv
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    yum install -y openssl openssl-devel libffi-devel python3-devel gcc
    yum install -y python3-pip
elif command -v apk &> /dev/null; then
    # Alpine
    apk add --no-cache openssl openssl-dev libffi-dev python3-dev build-base pkgconfig
    apk add --no-cache py3-pip
fi

# 2. Fix the grep warnings in init.sh
echo "Fixing grep warnings in init.sh..."
if [ -f "/volume/iPanel/init.sh" ]; then
    # Fix the stray backslashes in grep patterns
    sed -i 's/\\!/!/g' /volume/iPanel/init.sh
elif [ -f "./init.sh" ]; then
    sed -i 's/\\!/!/g' ./init.sh
fi

# 3. Create proper Python virtual environment
echo "Setting up Python virtual environment..."
PANEL_DIR="/www/server/panel"
if [ ! -d "$PANEL_DIR" ]; then
    mkdir -p "$PANEL_DIR"
fi

cd "$PANEL_DIR"

# Remove old pyenv if it exists and has issues
if [ -d "pyenv" ]; then
    echo "Removing problematic pyenv directory..."
    rm -rf pyenv
fi

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv pyenv

# Activate virtual environment
source pyenv/bin/activate

# Upgrade pip and install basic requirements
echo "Upgrading pip and installing basic requirements..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies that were failing
echo "Installing Python dependencies..."
pip install psutil
pip install bcrypt
pip install cachelib

# Install other common dependencies for iPanel
pip install flask
pip install requests
pip install paramiko
pip install cryptography

# 4. Fix the init script reference
echo "Fixing init script references..."
if [ ! -f "/etc/init.d/bt" ]; then
    # Create a symlink or copy the init script
    if [ -f "$PANEL_DIR/init.sh" ]; then
        cp "$PANEL_DIR/init.sh" /etc/init.d/bt
        chmod +x /etc/init.d/bt
    elif [ -f "/volume/iPanel/init.sh" ]; then
        cp /volume/iPanel/init.sh /etc/init.d/bt
        chmod +x /etc/init.d/bt
    fi
fi

# 5. Create missing directories
echo "Creating missing directories..."
mkdir -p /www/server/panel/logs
mkdir -p /www/server/panel/data
mkdir -p /www/server/panel/config

# 6. Set proper permissions
echo "Setting proper permissions..."
chmod +x "$PANEL_DIR/init.sh" 2>/dev/null || true
chmod +x /etc/init.d/bt 2>/dev/null || true

# 7. Fix the tools.py import issue
echo "Fixing tools.py import issue..."
if [ -f "$PANEL_DIR/tools.py" ]; then
    # Ensure the virtual environment is used
    sed -i '1i#!/www/server/panel/pyenv/bin/python' "$PANEL_DIR/tools.py"
fi

echo "=== Installation fixes completed ==="
echo "Please run the installation script again."
echo "If you continue to have issues, run this script as root (sudo)."
