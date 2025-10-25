#!/usr/bin/env python3
"""Quick test of Niimbot BLE service"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.niimbot_printer_ble import NiimbotPrinterBLE

async def test():
    address = sys.argv[1] if len(sys.argv) > 1 else "B1"
    
    print(f"Testing connection to {address}...")
    
    async with NiimbotPrinterBLE(address) as printer:
        if not printer.connected:
            print("❌ Connection failed")
            return
        
        print("✅ Connected!")
        
        # Test heartbeat
        print("\nTesting heartbeat...")
        hb = await printer.send_heartbeat()
        if hb:
            print(f"✅ Heartbeat OK: {hb.data.hex()}")
        
        # Test RFID
        print("\nGetting RFID info...")
        rfid = await printer.get_rfid()
        if rfid:
            print(f"✅ RFID detected:")
            print(f"   Barcode: {rfid.get('barcode', 'N/A')}")
            print(f"   Serial: {rfid.get('serial', 'N/A')}")
        else:
            print("⚠️  No RFID tag (no label loaded?)")

if __name__ == "__main__":
    asyncio.run(test())
