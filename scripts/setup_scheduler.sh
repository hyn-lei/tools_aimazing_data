#!/bin/bash

# Setup script for Scheduler Service
# usage: sudo ./setup_scheduler.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing Scheduler Service from $SCRIPT_DIR to $SYSTEMD_DIR..."

# Copy service file
if [ ! -f "$SCRIPT_DIR/aimazing-scheduler.service" ]; then
    echo "Error: aimazing-scheduler.service not found in $SCRIPT_DIR"
    exit 1
fi
cp "$SCRIPT_DIR/aimazing-scheduler.service" "$SYSTEMD_DIR/"

# Reload daemons
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting aimazing-scheduler..."
systemctl enable aimazing-scheduler
systemctl start aimazing-scheduler

echo "Status of aimazing-scheduler:"
systemctl status aimazing-scheduler --no-pager

echo "Done! Scheduler service installed and started."
