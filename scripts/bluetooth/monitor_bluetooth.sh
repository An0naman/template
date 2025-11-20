#!/bin/bash
# Bluetooth packet capture with live monitoring

CAPTURE_FILE="/home/an0naman/Documents/GitHub/template/btmon_capture.txt"

echo "=========================================="
echo "Bluetooth Traffic Monitor"
echo "=========================================="
echo ""
echo "Starting btmon capture..."
echo "Capture file: $CAPTURE_FILE"
echo ""
echo "Instructions:"
echo "1. Open the official Niimbot app on your phone"
echo "2. Connect to your B1 printer"
echo "3. Print a small test label"
echo "4. Press Ctrl+C here when done"
echo ""
echo "Monitoring activity (you'll see packets appear below):"
echo "------------------------------------------"
echo ""

# Start btmon with filtering for our printer and show activity
sudo btmon --write "$CAPTURE_FILE" 2>&1 | grep --line-buffered -E "HCI|ATT|GATT|13:07:12|ACL Data|Write|Read|Notification" | while read line; do
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $line"
done
