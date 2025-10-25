#!/usr/bin/env python3
"""
Test different packet formats for Niimbot B1
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"
WRITE_UUID = "49535343-8841-43f4-a8d4-ecbe34729bb3"
NOTIFY_UUID = "49535343-1e4d-4bd9-ba61-23c647249616"


async def test_packets():
    """Test different packet formats"""
    logger.info("=" * 70)
    logger.info("TESTING DIFFERENT PACKET FORMATS")
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
        
        # Test different packet formats
        packets_to_test = [
            {
                'name': 'Standard NiimPrintX Heartbeat',
                'packet': bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA]),
                'description': '55 55 DC 02 01 DD AA AA'
            },
            {
                'name': 'Get Device Info',
                'packet': bytes([0x55, 0x55, 0x40, 0x02, 0x08, 0x48, 0xAA, 0xAA]),
                'description': '55 55 40 02 08 48 AA AA (Get device type)'
            },
            {
                'name': 'Get Battery Level',
                'packet': bytes([0x55, 0x55, 0x40, 0x02, 0x0A, 0x4A, 0xAA, 0xAA]),
                'description': '55 55 40 02 0A 4A AA AA (Get battery)'
            },
            {
                'name': 'Alternative Heartbeat',
                'packet': bytes([0x55, 0x55, 0xDC, 0x01, 0xDC, 0xAA, 0xAA]),
                'description': '55 55 DC 01 DC AA AA (no data byte)'
            },
            {
                'name': 'Simple Status Check',
                'packet': bytes([0x55, 0x55, 0xA3, 0x02, 0x01, 0xA4, 0xAA, 0xAA]),
                'description': '55 55 A3 02 01 A4 AA AA (Get print status)'
            },
        ]
        
        for i, test in enumerate(packets_to_test, 1):
            logger.info(f"\n[Test {i}/{len(packets_to_test)}] {test['name']}")
            logger.info(f"  Format: {test['description']}")
            logger.info(f"  📤 Sending: {test['packet'].hex()}")
            
            response_received.clear()
            response_data.clear()
            
            try:
                await client.write_gatt_char(WRITE_UUID, test['packet'])
                
                # Wait for response
                await asyncio.wait_for(response_received.wait(), timeout=3.0)
                
                if response_data:
                    logger.info(f"  ✅ GOT RESPONSE!")
                    data = response_data[0]
                    logger.info(f"     Length: {len(data)} bytes")
                    logger.info(f"     Hex: {data.hex()}")
                    
                    # Try to parse
                    if len(data) >= 4:
                        logger.info(f"     Header: {data[0:2].hex()}")
                        logger.info(f"     Command: 0x{data[2]:02x}")
                        if len(data) > 3:
                            logger.info(f"     Length: {data[3]}")
                        if len(data) >= 7:
                            logger.info(f"     Footer: {data[-2:].hex()}")
                    
                    logger.info("\n  🎉 THIS PACKET FORMAT WORKS!")
                    break
                    
            except asyncio.TimeoutError:
                logger.info(f"  ⏱️  Timeout (no response)")
            except Exception as e:
                logger.info(f"  ❌ Error: {e}")
            
            await asyncio.sleep(0.5)
        
        await client.stop_notify(NOTIFY_UUID)
        
    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_packets())
