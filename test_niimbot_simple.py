#!/usr/bin/env python3
"""
Simple test script to verify Niimbot printer communication
Run directly on host for best Bluetooth access
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"


async def test_connection():
    """Test printer connection and find characteristics"""
    logger.info("=" * 70)
    logger.info("NIIMBOT B1 CONNECTION TEST")
    logger.info("=" * 70)
    logger.info(f"\nConnecting to: {PRINTER_ADDRESS}")
    
    async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
        if not client.is_connected:
            logger.error("❌ Failed to connect!")
            return
        
        logger.info("✅ Connected successfully!\n")
        
        # Show all services and characteristics
        logger.info("📋 GATT Services:")
        logger.info("-" * 70)
        
        fff1_uuid = None
        fff2_uuid = None
        
        for service in client.services:
            logger.info(f"\n🔧 Service: {service.uuid}")
            
            for char in service.characteristics:
                props = ', '.join(char.properties)
                logger.info(f"   📝 {char.uuid}")
                logger.info(f"      Properties: {props}")
                
                # Save B1 characteristics or fff1/fff2 if found
                if '49535343-8841-43f4-a8d4-ecbe34729bb3' in char.uuid.lower():
                    fff1_uuid = char.uuid
                    logger.info("      ⭐ This is B1 Write characteristic")
                elif '49535343-1e4d-4bd9-ba61-23c647249616' in char.uuid.lower():
                    fff2_uuid = char.uuid
                    logger.info("      ⭐ This is B1 Notify characteristic")
                elif 'fff1' in char.uuid.lower():
                    fff1_uuid = char.uuid
                    logger.info("      ⭐ This is FFF1 (Write characteristic)")
                elif 'fff2' in char.uuid.lower():
                    fff2_uuid = char.uuid
                    logger.info("      ⭐ This is FFF2 (Notify characteristic)")
        
        # Test communication
        logger.info("\n" + "=" * 70)
        logger.info("TESTING COMMUNICATION")
        logger.info("=" * 70)
        
        if not fff1_uuid or not fff2_uuid:
            logger.error("❌ Could not find FFF1 or FFF2 characteristics!")
            logger.error("   Your printer might use different UUIDs")
            return
        
        logger.info(f"\n✓ Write characteristic: {fff1_uuid}")
        logger.info(f"✓ Notify characteristic: {fff2_uuid}")
        
        # Set up notification handler
        response_received = asyncio.Event()
        response_data = []
        
        def notification_handler(sender, data):
            logger.info(f"\n📨 RECEIVED: {data.hex()}")
            response_data.append(data)
            response_received.set()
        
        await client.start_notify(fff2_uuid, notification_handler)
        logger.info("\n✓ Notifications enabled\n")
        
        # Send heartbeat command
        # Format: 55 55 DC 02 01 DD AA AA
        # DC = heartbeat command, 02 = length, 01 = data, DD = checksum
        heartbeat_packet = bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])
        
        logger.info(f"📤 SENDING HEARTBEAT: {heartbeat_packet.hex()}")
        await client.write_gatt_char(fff1_uuid, heartbeat_packet)
        
        # Wait for response
        try:
            await asyncio.wait_for(response_received.wait(), timeout=5.0)
            if response_data:
                data = response_data[0]
                logger.info(f"\n✅ SUCCESS! Printer responded!")
                logger.info(f"   Response length: {len(data)} bytes")
                logger.info(f"   Raw data: {data.hex()}")
                
                # Parse response if it follows NiimPrintX protocol
                if len(data) >= 7 and data[0:2] == b'\x55\x55' and data[-2:] == b'\xaa\xaa':
                    cmd = data[2]
                    length = data[3]
                    payload = data[4:4+length-1]
                    logger.info(f"\n   Parsed response:")
                    logger.info(f"   - Command: 0x{cmd:02x}")
                    logger.info(f"   - Length: {length}")
                    logger.info(f"   - Payload: {payload.hex()}")
            else:
                logger.warning("\n⚠️  Notification received but no data")
        except asyncio.TimeoutError:
            logger.error("\n❌ TIMEOUT - No response from printer")
            logger.error("   Possible issues:")
            logger.error("   1. Wrong characteristic UUIDs")
            logger.error("   2. Printer not ready/paired")
            logger.error("   3. Protocol mismatch")
        
        await client.stop_notify(fff2_uuid)
        
    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_connection())
