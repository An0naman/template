#!/usr/bin/env python3
"""
Try various protocol variants on D110
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

D110_ADDRESS = "C3:33:D5:02:36:62"
D110_CHAR = "bef8d6c9-9c21-4c9e-b632-bd58c1009f9f"


async def test_protocol_variants():
    """Try different protocol variants"""
    logger.info("=" * 70)
    logger.info("TESTING PROTOCOL VARIANTS ON D110")
    logger.info("=" * 70)
    
    async with BleakClient(D110_ADDRESS, timeout=30.0) as client:
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
        
        await client.start_notify(D110_CHAR, notification_handler)
        logger.info("✓ Notifications enabled\n")
        
        # Try various packet formats
        tests = [
            ("Standard heartbeat", bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])),
            ("No data byte", bytes([0x55, 0x55, 0xDC, 0x01, 0xDC, 0xAA, 0xAA])),
            ("Get info 0x08", bytes([0x55, 0x55, 0x40, 0x02, 0x08, 0x48, 0xAA, 0xAA])),
            ("Get info 0x0A", bytes([0x55, 0x55, 0x40, 0x02, 0x0A, 0x4A, 0xAA, 0xAA])),
            ("Simple 0x01", bytes([0x55, 0x55, 0x01, 0x01, 0x01, 0xAA, 0xAA])),
            ("Alt header FF", bytes([0xFF, 0xFF, 0xDC, 0x02, 0x01, 0xDD, 0xFF, 0xFF])),
            ("Single 0x55", bytes([0x55, 0xDC, 0x01, 0xDC, 0xAA])),
            ("Text HELLO", b"HELLO\r\n"),
            ("Text AT", b"AT\r\n"),
            ("Raw 0xDC", bytes([0xDC])),
            ("Raw 0x01", bytes([0x01])),
            ("Raw 0xFF", bytes([0xFF])),
        ]
        
        for name, packet in tests:
            logger.info(f"\n[{name}]")
            logger.info(f"  📤 {packet.hex() if len(packet) < 20 else packet[:20].hex() + '...'}")
            
            response_received.clear()
            response_data.clear()
            
            try:
                await client.write_gatt_char(D110_CHAR, packet, response=False)
                
                try:
                    await asyncio.wait_for(response_received.wait(), timeout=1.5)
                    logger.info(f"  ✅ GOT RESPONSE! This packet works!")
                    break
                except asyncio.TimeoutError:
                    logger.info(f"  ⏱️  No response")
                    
            except Exception as e:
                logger.info(f"  ❌ Error: {e}")
            
            await asyncio.sleep(0.3)
        
        await client.stop_notify(D110_CHAR)
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_protocol_variants())
