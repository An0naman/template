#!/bin/bash
# scripts/install_cleanup_service.sh
# Installs the docker-cleanup systemd service

set -e

SERVICE_NAME="docker-cleanup.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SERVICE="${SCRIPT_DIR}/${SERVICE_NAME}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo)"
  exit 1
fi

echo "Installing ${SERVICE_NAME}..."

# Copy service file
cp "${SOURCE_SERVICE}" "${SERVICE_PATH}"

# Reload systemd
systemctl daemon-reload

# Enable the service to run on boot
systemctl enable "${SERVICE_NAME}"

echo "Service installed and enabled."
echo "It will run automatically on the next reboot."
echo "To run it now manually: sudo systemctl start ${SERVICE_NAME}"
