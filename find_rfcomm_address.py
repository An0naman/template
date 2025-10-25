#!/usr/bin/env python3
"""Try to find the B1's RFCOMM address"""

import socket
import time

# Known BLE address
ble_address = "13:07:12:A6:40:07"
parts = ble_address.split(":")

print(f"Known BLE address: {ble_address}")
print(f"Trying rotated variations for RFCOMM...\n")

# Generate potential RFCOMM addresses based on byte rotation pattern
candidates = [
    # Original
    ble_address,
    # Rotate first 3 bytes to end
    f"{parts[3]}:{parts[4]}:{parts[5]}:{parts[0]}:{parts[1]}:{parts[2]}",
    # Rotate last 3 bytes to start  
    f"{parts[3]}:{parts[4]}:{parts[5]}:{parts[0]}:{parts[1]}:{parts[2]}",
    # Other patterns
    f"{parts[2]}:{parts[0]}:{parts[1]}:{parts[3]}:{parts[4]}:{parts[5]}",
    f"A6:40:07:13:07:12",
    f"07:A6:40:13:07:12",
]

# Remove duplicates
candidates = list(dict.fromkeys(candidates))

for addr in candidates:
    print(f"Trying {addr}...", end=" ")
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(3)
        sock.connect((addr, 1))
        print("✅ CONNECTED! This is the RFCOMM address!")
        sock.close()
        print(f"\n🎉 Found RFCOMM address: {addr}")
        print(f"   BLE address:  {ble_address}")
        print(f"   RFCOMM address: {addr}")
        break
    except Exception as e:
        print(f"❌ {str(e)[:40]}")
        time.sleep(0.5)
else:
    print("\n❌ Could not find RFCOMM address")
    print("\n💡 Options:")
    print("   1. The B1 may not support RFCOMM over this Bluetooth chip")
    print("   2. Try using the official app while running 'hcidump' to capture traffic")
    print("   3. The B1 might only support BLE (newer model?)")
    print("\n   If BLE is the only option, we need to capture the official app's")
    print("   Bluetooth traffic to see the exact protocol it uses.")
