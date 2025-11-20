#!/usr/bin/env python3
"""
Check D110 connection status and try to wake it up
"""

import asyncio
import logging
from bleak import BleakClient, BleakScanner

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"


async def check_d110_status():
    """Check if D110 is actually ready"""
    logger.info("=" * 70)
    logger.info("NIIMBOT D110 STATUS CHECK")
    logger.info("=" * 70)
    
    # First, scan to see current status
    logger.info("\n1. Scanning for printer...")
    devices = await BleakScanner.discover(timeout=5.0)
    
    found = False
    for device in devices:
        if device.address == PRINTER_ADDRESS:
            found = True
            logger.info(f"   ✓ Found: {device.name}")
            logger.info(f"   Address: {device.address}")
            if hasattr(device, 'rssi'):
                logger.info(f"   Signal: {device.rssi} dBm")
            if hasattr(device, 'metadata'):
                logger.info(f"   Metadata: {device.metadata}")
            break
    
    if not found:
        logger.error("   ✗ Printer not found in scan!")
        logger.error("   Make sure the printer is:")
        logger.error("     - Turned ON")
        logger.error("     - Has paper loaded")
        logger.error("     - Blue light is blinking (pairing mode)")
        return
    
    logger.info("\n2. Attempting connection...")
    
    try:
        async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
            if not client.is_connected:
                logger.error("   ✗ Connection failed")
                return
            
            logger.info("   ✓ Connected successfully")
            
            # Check services
            logger.info("\n3. Checking GATT services...")
            service_count = len(list(client.services))
            logger.info(f"   Found {service_count} services")
            
            # Look for the D110 service
            d110_service_uuid = "49535343-fe7d-4ae5-8fa9-9fafd205e455"
            d110_service = None
            
            for service in client.services:
                if service.uuid.lower() == d110_service_uuid.lower():
                    d110_service = service
                    logger.info(f"   ✓ Found D110 service: {service.uuid}")
                    break
            
            if not d110_service:
                logger.error(f"   ✗ Could not find D110 service {d110_service_uuid}")
                logger.error("   This might not be a D110, or it's not initialized")
                return
            
            # Get characteristics
            logger.info("\n4. Checking D110 characteristics...")
            write_char = None
            notify_char = None
            
            for char in d110_service.characteristics:
                logger.info(f"   {char.uuid}: {', '.join(char.properties)}")
                
                if char.uuid == "49535343-8841-43f4-a8d4-ecbe34729bb3":
                    write_char = char
                    logger.info("      ⭐ This is the WRITE characteristic")
                elif char.uuid == "49535343-1e4d-4bd9-ba61-23c647249616":
                    notify_char = char
                    logger.info("      ⭐ This is the NOTIFY characteristic")
            
            if not write_char or not notify_char:
                logger.error("   ✗ Missing write or notify characteristic")
                return
            
            logger.info("\n5. Testing button press detection...")
            logger.info("   Please press the button on the D110 printer NOW...")
            logger.info("   (Waiting 10 seconds...)")
            
            button_pressed = asyncio.Event()
            
            def notification_handler(sender, data):
                logger.info(f"   📨 Received: {data.hex()}")
                button_pressed.set()
            
            await client.start_notify(notify_char.uuid, notification_handler)
            
            try:
                await asyncio.wait_for(button_pressed.wait(), timeout=10.0)
                logger.info("\n   ✅ Printer responded to button press!")
                logger.info("   The printer is working and can communicate!")
            except asyncio.TimeoutError:
                logger.warning("\n   ⚠️  No response from button press")
                logger.warning("   Possible issues:")
                logger.warning("     - Printer is in deep sleep mode")
                logger.warning("     - Paper not loaded")
                logger.warning("     - Battery too low")
                logger.warning("     - Needs to be paired through official app first")
            
            await client.stop_notify(notify_char.uuid)
            
            logger.info("\n6. Trying to wake up printer with commands...")
            
            # Try multiple wake-up sequences
            wake_commands = [
                ("Heartbeat", bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])),
                ("Get Info", bytes([0x55, 0x55, 0x40, 0x02, 0x08, 0x48, 0xAA, 0xAA])),
                ("Get Battery", bytes([0x55, 0x55, 0x40, 0x02, 0x0A, 0x4A, 0xAA, 0xAA])),
            ]
            
            response_event = asyncio.Event()
            response_data = []
            
            def wake_handler(sender, data):
                logger.info(f"      📨 Response: {data.hex()}")
                response_data.append(data)
                response_event.set()
            
            await client.start_notify(notify_char.uuid, wake_handler)
            
            for name, cmd in wake_commands:
                logger.info(f"   Trying {name}...")
                response_event.clear()
                response_data.clear()
                
                try:
                    await client.write_gatt_char(write_char.uuid, cmd)
                    await asyncio.wait_for(response_event.wait(), timeout=2.0)
                    
                    if response_data:
                        logger.info(f"   ✅ SUCCESS! Printer responded to {name}!")
                        logger.info(f"      Response: {response_data[0].hex()}")
                        break
                except asyncio.TimeoutError:
                    logger.info(f"      No response")
            
            await client.stop_notify(notify_char.uuid)
            
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n" + "=" * 70)
    logger.info("DIAGNOSTIC COMPLETE")
    logger.info("=" * 70)
    logger.info("\nRECOMMENDATIONS:")
    logger.info("1. Make sure printer is ON and has paper loaded")
    logger.info("2. Try turning printer OFF and ON again")
    logger.info("3. Make sure battery is charged")
    logger.info("4. Try pairing through the official Niimbot app first")
    logger.info("5. Press the printer button to wake it from sleep mode")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(check_d110_status())
