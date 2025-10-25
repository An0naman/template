#!/usr/bin/env python3
"""
Monitor ALL characteristics for ANY activity
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"


async def monitor_all():
    """Monitor all notify-capable characteristics and try writing"""
    logger.info("=" * 70)
    logger.info("MONITORING ALL CHARACTERISTICS")
    logger.info("=" * 70)
    
    async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
        if not client.is_connected:
            logger.error("❌ Failed to connect!")
            return
        
        logger.info("✅ Connected\n")
        
        # Find all notify-capable characteristics
        notify_chars = []
        write_chars = []
        
        for service in client.services:
            for char in service.characteristics:
                if 'notify' in char.properties or 'indicate' in char.properties:
                    notify_chars.append((char.uuid, char))
                    logger.info(f"✓ Notify characteristic: {char.uuid}")
                if 'write' in char.properties or 'write-without-response' in char.properties:
                    write_chars.append((char.uuid, char))
        
        logger.info(f"\nFound {len(notify_chars)} notify characteristics")
        logger.info(f"Found {len(write_chars)} write characteristics\n")
        
        # Set up handlers for ALL notify characteristics
        received_any = asyncio.Event()
        
        def make_handler(uuid):
            def handler(sender, data):
                logger.info(f"📨 {uuid}: {data.hex()}")
                received_any.set()
            return handler
        
        for uuid, char in notify_chars:
            try:
                await client.start_notify(uuid, make_handler(uuid))
                logger.info(f"✓ Monitoring: {uuid}")
            except Exception as e:
                logger.info(f"✗ Could not monitor {uuid}: {e}")
        
        logger.info("\n" + "=" * 70)
        logger.info("NOW SENDING TEST PACKETS TO ALL WRITE CHARACTERISTICS")
        logger.info("=" * 70 + "\n")
        
        # Try a simple packet to each write characteristic
        test_packet = bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])
        
        for uuid, char in write_chars:
            logger.info(f"\n📤 Writing to: {uuid}")
            logger.info(f"   Packet: {test_packet.hex()}")
            
            try:
                received_any.clear()
                await client.write_gatt_char(uuid, test_packet)
                
                # Wait a moment
                try:
                    await asyncio.wait_for(received_any.wait(), timeout=2.0)
                    logger.info("   ✅ GOT A RESPONSE!")
                except asyncio.TimeoutError:
                    logger.info("   ⏱️  No response")
            except Exception as e:
                logger.info(f"   ❌ Error: {e}")
            
            await asyncio.sleep(0.5)
        
        logger.info("\n" + "=" * 70)
        logger.info("Waiting 5 seconds to see if printer sends anything spontaneously...")
        logger.info("=" * 70)
        
        try:
            await asyncio.wait_for(received_any.wait(), timeout=5.0)
            logger.info("\n📨 Received spontaneous data!")
        except asyncio.TimeoutError:
            logger.info("\n⏱️  No spontaneous data")
        
        # Clean up
        for uuid, char in notify_chars:
            try:
                await client.stop_notify(uuid)
            except:
                pass
    
    logger.info("\n" + "=" * 70)
    logger.info("MONITORING COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(monitor_all())
