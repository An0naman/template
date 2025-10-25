#!/usr/bin/env python3
"""
Bluetooth Packet Capture Guide for Niimbot Printers

This script helps you capture the Bluetooth communication between 
the official Niimbot app and your printer, so we can reverse-engineer 
the protocol.

INSTRUCTIONS:
=============

METHOD 1: Using Android Phone (Easiest)
----------------------------------------
1. Enable Developer Options on your Android phone:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings > Developer Options

2. Enable Bluetooth HCI Snoop Log:
   - In Developer Options, enable "Bluetooth HCI snoop log"

3. Print something using the official Niimbot app
   - Connect to your printer
   - Print a test label

4. Get the capture file:
   - The log is saved to: /sdcard/Android/data/btsnoop_hci.log
   - Or use: adb pull /sdcard/Android/data/btsnoop_hci.log

5. Analyze with Wireshark:
   - Open the .log file in Wireshark
   - Filter by Bluetooth address of your printer
   - Look for ATT (Attribute Protocol) packets


METHOD 2: Using btmon on Linux (Advanced)
------------------------------------------
1. Stop Bluetooth:
   sudo systemctl stop bluetooth

2. Start btmon (in one terminal):
   sudo btmon -w /tmp/niimbot_capture.log

3. Start Bluetooth (in another terminal):
   sudo systemctl start bluetooth

4. Use the official Niimbot app to print

5. Stop btmon (Ctrl+C)

6. Analyze with Wireshark:
   wireshark /tmp/niimbot_capture.log


WHAT TO LOOK FOR:
=================
- Write commands to characteristic UUIDs
- The packet format (header, data, checksum, footer)
- Command sequences (initialization, status check, print)
- Image data encoding


ALTERNATIVE: Quick Test
========================
If you can't capture packets, try this:
1. Make sure printer is ON and in pairing mode (blue light)
2. Open official app and connect
3. Try printing from official app
4. If it works, the printer is ready
5. Run our test scripts again while printer is still "warmed up"

"""

import asyncio
from bleak import BleakScanner

async def quick_scan():
    print("\n" + "="*70)
    print("QUICK PRINTER SCAN")
    print("="*70)
    print("\nScanning for Niimbot printers...")
    print("Make sure printer is ON and in pairing mode!\n")
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    niimbot_found = False
    for device in devices:
        if device.name and ('niimbot' in device.name.lower() or 
                           'b1' in device.name.lower() or 
                           'd110' in device.name.lower() or
                           'd11' in device.name.lower()):
            print(f"✓ Found: {device.name}")
            print(f"  Address: {device.address}")
            print(f"  RSSI: {device.rssi if hasattr(device, 'rssi') else 'N/A'}")
            niimbot_found = True
    
    if not niimbot_found:
        print("✗ No Niimbot printers found")
        print("  Make sure printer is ON and in pairing mode (blue light)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    print(__doc__)
    print("\nRunning quick scan...\n")
    asyncio.run(quick_scan())
