#!/bin/bash
# Simple Bluetooth monitor with status feedback

CAPTURE_FILE="/home/an0naman/Documents/GitHub/template/btmon_capture.txt"

echo "=========================================="
echo "Bluetooth Traffic Monitor v2"
echo "=========================================="
echo ""
echo "This will capture ALL Bluetooth traffic."
echo "You'll need to enter your sudo password."
echo ""

# Test sudo first
sudo -v
if [ $? -ne 0 ]; then
    echo "❌ Password incorrect or sudo failed"
    exit 1
fi

echo "✅ Password accepted! Starting btmon..."
echo ""
echo "📡 Now monitoring Bluetooth traffic..."
echo "   Any activity will appear below:"
echo "------------------------------------------"

# Run btmon with simple output
sudo btmon 2>&1 | tee "$CAPTURE_FILE" | grep --line-buffered -i "13:07\|b1\|niim\|att \|gatt\|write\|notification" | while read line; do
    echo "[$(date '+%H:%M:%S')] $line"
done

echo ""
echo "Monitor stopped. Check $CAPTURE_FILE for full capture."
