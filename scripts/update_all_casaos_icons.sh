#!/bin/bash
#
# Update CasaOS Icons for All Template Apps
# Scans for all running template-based apps and updates their icons
#
# Usage:
#   sudo ./update_all_casaos_icons.sh
#

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CasaOS Icon Updater - Batch Mode                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${GREEN}ℹ${NC} This script must be run as root (use sudo)"
    exit 1
fi

CASAOS_APPS_DIR="/var/lib/casaos/apps"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if CasaOS is installed
if [ ! -d "$CASAOS_APPS_DIR" ]; then
    echo "CasaOS not found at $CASAOS_APPS_DIR"
    exit 1
fi

# Find all app metadata files
echo "Scanning for CasaOS apps..."
echo

APPS_FOUND=0
APPS_UPDATED=0

for metadata_file in "$CASAOS_APPS_DIR"/*.json; do
    if [ ! -f "$metadata_file" ]; then
        continue
    fi
    
    app_name=$(basename "$metadata_file" .json)
    APPS_FOUND=$((APPS_FOUND + 1))
    
    # Try to detect port from the metadata
    port=$(jq -r '.port_map // "5001"' "$metadata_file" 2>/dev/null)
    
    echo -e "${BLUE}→${NC} Processing: ${app_name} (port: ${port})"
    
    # Run the update script
    if "$SCRIPT_DIR/update_casaos_icon.sh" "$app_name" "$port" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓${NC} Updated successfully"
        APPS_UPDATED=$((APPS_UPDATED + 1))
    else
        echo "  ⚠ Skipped (may not have /api/logo endpoint)"
    fi
    echo
done

echo
echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Summary                                          ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Apps found:    $APPS_FOUND"
echo -e "${GREEN}║${NC}  Apps updated:  $APPS_UPDATED"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"

if [ "$APPS_UPDATED" -gt 0 ]; then
    echo
    echo "Refresh your CasaOS web interface to see the changes."
    echo "If icons don't update, try: sudo systemctl restart casaos"
fi

exit 0
