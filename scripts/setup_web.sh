#!/bin/bash

# Setup script for Web App Service
# usage: sudo ./setup_web.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing Web App Service from $SCRIPT_DIR to $SYSTEMD_DIR..."

# Copy service file
if [ ! -f "$SCRIPT_DIR/aimazing-web.service" ]; then
    echo "Error: aimazing-web.service not found in $SCRIPT_DIR"
    exit 1
fi

cp "$SCRIPT_DIR/aimazing-web.service" "$SYSTEMD_DIR/"

# Reload daemons
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting aimazing-web..."
systemctl enable aimazing-web
systemctl start aimazing-web

echo "Status of aimazing-web:"
systemctl status aimazing-web --no-pager

echo "Done! Web App service installed and started."
