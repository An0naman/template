#!/usr/bin/env python3
"""
Fresh BLE scan and connection test
"""

import asyncio
from bleak import BleakScanner, BleakClient

async def scan_and_connect():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    print(f"\nFound {len(devices)} devices:")
    printer_device = None
    for device in devices:
        print(f"  {device.address} - {device.name}")
        # Look for either B1 or D110
        if device.address in ["13:07:12:A6:40:07", "C3:33:D5:02:36:62"] or \
           (device.name and ("B1" in device.name or "D110" in device.name)):
            printer_device = device
            print(f"    ⭐ Found Niimbot printer!")
    
    if not printer_device:
        print("\n❌ Niimbot printer not found in scan")
        return
    
    print(f"\n✅ Connecting to {printer_device.address} ({printer_device.name})...")
    async with BleakClient(printer_device.address) as client:
        print("✅ Connected!")
        
        # Show all services and characteristics
        print("\n📋 Services and Characteristics:")
        for service in client.services:
            print(f"\n  Service: {service.uuid}")
            for char in service.characteristics:
                print(f"    Char: {char.uuid} - {', '.join(char.properties)}")
        
        # Try to find write and notify characteristics
        # Prefer characteristic with both write and notify
        write_uuid = None
        notify_uuid = None
        rw_notify_uuid = None
        
        for service in client.services:
            for char in service.characteristics:
                # Look for characteristic with read, write, AND notify
                if 'write' in char.properties and 'notify' in char.properties:
                    rw_notify_uuid = char.uuid
                    print(f"    ⭐ Found R/W/Notify char: {char.uuid}")
                elif 'write' in char.properties and not write_uuid:
                    write_uuid = char.uuid
                elif 'notify' in char.properties and not notify_uuid:
                    notify_uuid = char.uuid
        
        # Prefer the combined R/W/Notify characteristic
        if rw_notify_uuid:
            write_uuid = rw_notify_uuid
            notify_uuid = rw_notify_uuid
            print(f"\n✓ Using combined R/W/Notify characteristic: {rw_notify_uuid}")
        elif write_uuid and notify_uuid:
            print(f"\n✓ Using separate characteristics:")
            print(f"   Write: {write_uuid}")
            print(f"   Notify: {notify_uuid}")
        else:
            print(f"\n⚠️  Could not find write/notify characteristics")
            print(f"     Write: {write_uuid}")
            print(f"     Notify: {notify_uuid}")
            return
        
        response_received = asyncio.Event()
        
        def handler(sender, data):
            print(f"📨 Response: {data.hex()}")
            response_received.set()
        
        await client.start_notify(notify_uuid, handler)
        print("✓ Notifications started")
        
        # Send heartbeat with correct checksum
        # Format: 55 55 <cmd> <len> <data> <checksum> AA AA
        # Checksum = cmd XOR len XOR data
        cmd = 0xDC
        data = bytes([0x01])
        length = len(data)
        checksum = cmd ^ length
        for byte in data:
            checksum ^= byte
        
        packet = bytes([0x55, 0x55, cmd, length, *data, checksum, 0xAA, 0xAA])
        print(f"📤 Sending heartbeat: {packet.hex()}")
        print(f"   Checksum calculated: 0x{checksum:02x}")
        await client.write_gatt_char(write_uuid, packet)
        
        try:
            await asyncio.wait_for(response_received.wait(), timeout=5.0)
            print("✅ GOT RESPONSE!")
        except asyncio.TimeoutError:
            print("⏱️  Timeout")
        
        await client.stop_notify(notify_uuid)

if __name__ == "__main__":
    asyncio.run(scan_and_connect())
