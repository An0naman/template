#!/usr/bin/env python3
"""
Diagnostic tool for Niimbot printer Bluetooth communication
Run this directly on the host (not in Docker) for better Bluetooth access
"""

import asyncio
import logging
from bleak import BleakClient, BleakScanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"  # Your Niimbot B1


async def scan_printers():
    """Scan for Niimbot printers"""
    logger.info("Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    logger.info(f"\nFound {len(devices)} Bluetooth devices:")
    for device in devices:
        logger.info(f"  {device.name or 'Unknown'} - {device.address}")
        if device.name and ('niimbot' in device.name.lower() or 'b1' in device.name.lower()):
            logger.info(f"    ⭐ This looks like a Niimbot printer!")
    print()


async def inspect_printer(address: str):
    """Connect to printer and inspect its GATT services"""
    logger.info(f"Connecting to printer at {address}...")
    
    try:
        async with BleakClient(address, timeout=30.0) as client:
            if not client.is_connected:
                logger.error("Failed to connect!")
                return
            
            logger.info("✓ Connected successfully!\n")
            
            logger.info("=" * 70)
            logger.info("GATT SERVICES AND CHARACTERISTICS")
            logger.info("=" * 70)
            
            for service in client.services:
                logger.info(f"\n📦 Service: {service.uuid}")
                logger.info(f"   Description: {service.description}")
                
                for char in service.characteristics:
                    logger.info(f"\n   📝 Characteristic: {char.uuid}")
                    logger.info(f"      Properties: {', '.join(char.properties)}")
                    logger.info(f"      Description: {char.description}")
                    
                    # If readable, try to read
                    if 'read' in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            logger.info(f"      Value: {value.hex()}")
                        except Exception as e:
                            logger.info(f"      Value: (Error reading: {e})")
            
            logger.info("\n" + "=" * 70)
            logger.info("ANALYSIS")
            logger.info("=" * 70)
            
            # Find potential write/notify characteristics
            write_chars = []
            notify_chars = []
            
            for service in client.services:
                for char in service.characteristics:
                    if 'write' in char.properties or 'write-without-response' in char.properties:
                        write_chars.append((service.uuid, char.uuid, char.properties))
                    if 'notify' in char.properties:
                        notify_chars.append((service.uuid, char.uuid, char.properties))
            
            logger.info(f"\nFound {len(write_chars)} writable characteristic(s):")
            for svc, char, props in write_chars:
                logger.info(f"  • {char} (Service: {svc})")
                logger.info(f"    Properties: {', '.join(props)}")
            
            logger.info(f"\nFound {len(notify_chars)} notify characteristic(s):")
            for svc, char, props in notify_chars:
                logger.info(f"  • {char} (Service: {svc})")
                logger.info(f"    Properties: {', '.join(props)}")
            
            logger.info("\n" + "=" * 70)
            logger.info("RECOMMENDATIONS")
            logger.info("=" * 70)
            
            # Look for fff0 service
            fff0_service = None
            for service in client.services:
                if 'fff0' in service.uuid.lower():
                    fff0_service = service
                    break
            
            if fff0_service:
                logger.info("\n✓ Found 0000fff0 service (common for Niimbot printers)")
                fff1_char = None
                fff2_char = None
                
                for char in fff0_service.characteristics:
                    if 'fff1' in char.uuid.lower():
                        fff1_char = char
                    if 'fff2' in char.uuid.lower():
                        fff2_char = char
                
                if fff1_char:
                    logger.info(f"  Write characteristic (fff1): {fff1_char.uuid}")
                    logger.info(f"    Properties: {', '.join(fff1_char.properties)}")
                
                if fff2_char:
                    logger.info(f"  Notify characteristic (fff2): {fff2_char.uuid}")
                    logger.info(f"    Properties: {', '.join(fff2_char.properties)}")
                
                if fff1_char and fff2_char:
                    logger.info("\n✅ Configuration looks correct for Niimbot communication!")
                    logger.info(f"   Use {fff1_char.uuid} for writing commands")
                    logger.info(f"   Use {fff2_char.uuid} for receiving responses")
                else:
                    logger.info("\n⚠️  Expected fff1/fff2 characteristics not found")
            else:
                logger.info("\n⚠️  0000fff0 service not found")
                logger.info("   The printer might use a different service UUID")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def test_simple_command(address: str):
    """Test sending a simple command to the printer"""
    logger.info(f"\nTesting printer communication with {address}...")
    
    try:
        async with BleakClient(address, timeout=30.0) as client:
            if not client.is_connected:
                logger.error("Failed to connect!")
                return
            
            logger.info("✓ Connected\n")
            
            # Find fff1 (write) and fff2 (notify) characteristics
            fff1_uuid = None
            fff2_uuid = None
            
            for service in client.services:
                if 'fff0' in service.uuid.lower():
                    for char in service.characteristics:
                        if 'fff1' in char.uuid.lower():
                            fff1_uuid = char.uuid
                        if 'fff2' in char.uuid.lower():
                            fff2_uuid = char.uuid
            
            if not fff1_uuid:
                logger.error("Could not find write characteristic (fff1)")
                return
            
            logger.info(f"Using write characteristic: {fff1_uuid}")
            logger.info(f"Using notify characteristic: {fff2_uuid or 'N/A'}")
            
            # Set up notification handler
            notification_received = asyncio.Event()
            notification_data = []
            
            def handle_notification(sender, data):
                logger.info(f"📨 Received notification: {data.hex()}")
                notification_data.append(data)
                notification_received.set()
            
            if fff2_uuid:
                await client.start_notify(fff2_uuid, handle_notification)
                logger.info("✓ Started notifications\n")
            
            # Send heartbeat command (0xDC)
            # Packet format: 55 55 <cmd> <len> <data> <checksum> AA AA
            cmd = 0xDC
            data = bytes([0x01])
            length = len(data) + 1
            checksum = (cmd + sum(data)) & 0xFF
            packet = bytes([0x55, 0x55, cmd, length]) + data + bytes([checksum, 0xAA, 0xAA])
            
            logger.info(f"Sending heartbeat command: {packet.hex()}")
            await client.write_gatt_char(fff1_uuid, packet)
            
            # Wait for response
            try:
                await asyncio.wait_for(notification_received.wait(), timeout=5.0)
                if notification_data:
                    logger.info(f"\n✅ Printer responded! Data: {notification_data[0].hex()}")
                else:
                    logger.warning("\n⚠️  No response data received")
            except asyncio.TimeoutError:
                logger.error("\n❌ No response from printer (timeout)")
            
            if fff2_uuid:
                await client.stop_notify(fff2_uuid)
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def main():
    """Main diagnostic routine"""
    print("\n" + "=" * 70)
    print("NIIMBOT PRINTER DIAGNOSTIC TOOL")
    print("=" * 70)
    
    # Step 1: Scan for printers
    await scan_printers()
    
    # Step 2: Inspect the known printer
    print("\nPress Enter to inspect printer GATT services...")
    input()
    await inspect_printer(PRINTER_ADDRESS)
    
    # Step 3: Test communication
    print("\nPress Enter to test printer communication...")
    input()
    await test_simple_command(PRINTER_ADDRESS)
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
