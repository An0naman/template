#!/bin/bash
# Pair Niimbot printers with Linux Bluetooth

echo "================================="
echo "NIIMBOT PRINTER PAIRING GUIDE"
echo "================================="
echo ""
echo "Make sure your printer is ON and in pairing mode (blue light flashing)"
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "Scanning for Bluetooth devices..."
echo ""

# Start scanning
timeout 15 bluetoothctl --timeout 15 scan on &
SCAN_PID=$!
sleep 12

# List devices
echo ""
echo "Found devices:"
bluetoothctl devices

echo ""
echo "Enter the MAC address of your Niimbot printer (e.g., 13:07:12:A6:40:07): "
read MAC_ADDRESS

if [ -z "$MAC_ADDRESS" ]; then
    echo "No address entered. Exiting."
    exit 1
fi

echo ""
echo "Pairing with $MAC_ADDRESS..."
echo ""

# Pair and trust the device
bluetoothctl <<EOF
pair $MAC_ADDRESS
trust $MAC_ADDRESS
connect $MAC_ADDRESS
exit
EOF

echo ""
echo "================================="
echo "Pairing complete!"
echo "================================="
echo ""
echo "You can now use the printer with our app."
echo "The printer should remain paired even after disconnect."
echo ""
echo "To check pairing status: bluetoothctl info $MAC_ADDRESS"
echo ""
