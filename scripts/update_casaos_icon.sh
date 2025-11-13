#!/bin/bash
#
# CasaOS Icon Updater
# Automatically updates CasaOS app metadata to use the dynamic logo API
# with the correct IP address and port.
#
# Usage:
#   sudo ./update_casaos_icon.sh [app_name] [port]
#   sudo ./update_casaos_icon.sh template 5001
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
APP_NAME="${1:-template}"
PORT="${2:-5001}"
CASAOS_APPS_DIR="/var/lib/casaos/apps"
METADATA_FILE="${CASAOS_APPS_DIR}/${APP_NAME}.json"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if CasaOS is installed
if [ ! -d "$CASAOS_APPS_DIR" ]; then
    print_error "CasaOS apps directory not found: $CASAOS_APPS_DIR"
    print_info "Is CasaOS installed?"
    exit 1
fi

# Check if app metadata file exists
if [ ! -f "$METADATA_FILE" ]; then
    print_error "App metadata file not found: $METADATA_FILE"
    print_info "Available apps:"
    ls -1 "$CASAOS_APPS_DIR"/*.json 2>/dev/null | xargs -n1 basename | sed 's/.json$//' || echo "  (none)"
    exit 1
fi

print_info "Updating CasaOS icon for app: ${APP_NAME}"
echo

# Detect primary network interface and IP
print_info "Detecting network configuration..."

# Try to get the default route interface
DEFAULT_INTERFACE=$(ip route show default | head -1 | awk '{print $5}')
if [ -z "$DEFAULT_INTERFACE" ]; then
    print_warning "Could not detect default network interface"
    DEFAULT_INTERFACE="wlp0s20f3"  # Fallback
fi

print_info "Using network interface: ${DEFAULT_INTERFACE}"

# Get IP address for the interface
IP_ADDRESS=$(ip -4 addr show "$DEFAULT_INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)

if [ -z "$IP_ADDRESS" ]; then
    print_error "Could not detect IP address for interface: ${DEFAULT_INTERFACE}"
    print_info "Available interfaces:"
    ip -4 addr | grep -oP '^\d+:\s+\K[^:]+' | while read -r iface; do
        ip_addr=$(ip -4 addr show "$iface" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
        if [ -n "$ip_addr" ]; then
            echo "  - $iface: $ip_addr"
        fi
    done
    exit 1
fi

print_success "Detected IP address: ${IP_ADDRESS}"
echo

# Construct the new icon URL
NEW_ICON_URL="http://${IP_ADDRESS}:${PORT}/api/logo"
print_info "New icon URL: ${NEW_ICON_URL}"

# Backup the original file
BACKUP_FILE="${METADATA_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$METADATA_FILE" "$BACKUP_FILE"
print_success "Created backup: ${BACKUP_FILE}"

# Update the icon URL using jq (if available) or sed
if command -v jq &> /dev/null; then
    print_info "Using jq to update metadata..."
    jq --arg icon "$NEW_ICON_URL" '.icon = $icon' "$METADATA_FILE" > "${METADATA_FILE}.tmp"
    mv "${METADATA_FILE}.tmp" "$METADATA_FILE"
else
    print_info "Using sed to update metadata (jq not available)..."
    sed -i.tmp "s|\"icon\": \"[^\"]*\"|\"icon\": \"${NEW_ICON_URL}\"|g" "$METADATA_FILE"
    rm -f "${METADATA_FILE}.tmp"
fi

print_success "Updated ${METADATA_FILE}"
echo

# Verify the change
print_info "Verifying changes..."
if grep -q "$NEW_ICON_URL" "$METADATA_FILE"; then
    print_success "Icon URL successfully updated!"
    echo
    print_info "Updated metadata:"
    if command -v jq &> /dev/null; then
        jq '.icon' "$METADATA_FILE"
    else
        grep '"icon"' "$METADATA_FILE"
    fi
else
    print_error "Failed to update icon URL"
    print_info "Restoring from backup..."
    mv "$BACKUP_FILE" "$METADATA_FILE"
    exit 1
fi

echo
print_success "CasaOS icon updated successfully!"
print_info "You may need to refresh CasaOS web interface to see the changes."
print_info "If the icon doesn't update, try: sudo systemctl restart casaos"

exit 0
