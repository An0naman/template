#!/usr/bin/env python3
"""
Test B1 with write-without-response characteristic
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"
NOTIFY_UUID = "49535343-1e4d-4bd9-ba61-23c647249616"

# Try BOTH write characteristics
WRITE_UUID_WITH_RESPONSE = "49535343-8841-43f4-a8d4-ecbe34729bb3"
WRITE_UUID_WITHOUT_RESPONSE = "49535343-6daa-4d02-abf6-19569aca69fe"


async def test_both_write_chars():
    """Test both write characteristics"""
    logger.info("=" * 70)
    logger.info("TESTING BOTH WRITE CHARACTERISTICS")
    logger.info("=" * 70)
    
    async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
        if not client.is_connected:
            logger.error("❌ Failed to connect!")
            return
        
        logger.info("✅ Connected\n")
        
        response_received = asyncio.Event()
        response_data = []
        
        def notification_handler(sender, data):
            logger.info(f"   📨 RESPONSE: {data.hex()}")
            response_data.append(data)
            response_received.set()
        
        await client.start_notify(NOTIFY_UUID, notification_handler)
        logger.info("✓ Notifications enabled\n")
        
        # Packets to test
        packets = [
            ('Heartbeat', bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])),
            ('Get Info', bytes([0x55, 0x55, 0x40, 0x02, 0x08, 0x48, 0xAA, 0xAA])),
            ('Get Battery', bytes([0x55, 0x55, 0x40, 0x02, 0x0A, 0x4A, 0xAA, 0xAA])),
        ]
        
        for char_name, char_uuid in [
            ("Write (with response)", WRITE_UUID_WITH_RESPONSE),
            ("Write-without-response", WRITE_UUID_WITHOUT_RESPONSE)
        ]:
            logger.info(f"\n{'='*70}")
            logger.info(f"Testing: {char_name}")
            logger.info(f"UUID: {char_uuid}")
            logger.info(f"{'='*70}")
            
            for packet_name, packet in packets:
                logger.info(f"\n  [{packet_name}] 📤 {packet.hex()}")
                
                response_received.clear()
                response_data.clear()
                
                try:
                    await client.write_gatt_char(char_uuid, packet, response=('response' in char_name.lower()))
                    
                    await asyncio.wait_for(response_received.wait(), timeout=2.0)
                    
                    if response_data:
                        logger.info(f"  ✅ RESPONSE: {response_data[0].hex()}")
                        logger.info(f"\n  🎉 SUCCESS WITH {char_name}!")
                        return
                        
                except asyncio.TimeoutError:
                    logger.info(f"  ⏱️  No response")
                except Exception as e:
                    logger.info(f"  ❌ Error: {e}")
                
                await asyncio.sleep(0.3)
        
        await client.stop_notify(NOTIFY_UUID)
        
    logger.info("\n" + "=" * 70)
    logger.info("No working combination found")
    logger.info("The B1 might use a different protocol entirely")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_both_write_chars())
