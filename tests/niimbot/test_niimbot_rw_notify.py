#!/usr/bin/env python3
"""
Test the read/write/notify characteristic
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"
# This is the read/write/notify characteristic!
RW_NOTIFY_UUID = "49535343-aca3-481c-91ec-d85e28a60318"


async def test_rw_notify_char():
    """Test the read/write/notify characteristic"""
    logger.info("=" * 70)
    logger.info("TESTING READ/WRITE/NOTIFY CHARACTERISTIC")
    logger.info(f"UUID: {RW_NOTIFY_UUID}")
    logger.info("=" * 70)
    
    async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
        if not client.is_connected:
            logger.error("❌ Failed to connect!")
            return
        
        logger.info("✅ Connected\n")
        
        response_received = asyncio.Event()
        response_data = []
        
        def notification_handler(sender, data):
            logger.info(f"   📨 NOTIFICATION: {data.hex()}")
            response_data.append(data)
            response_received.set()
        
        # Start notifications on THIS characteristic
        await client.start_notify(RW_NOTIFY_UUID, notification_handler)
        logger.info("✓ Notifications enabled on read/write/notify characteristic\n")
        
        # Test packets
        packets = [
            ('Heartbeat', bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])),
            ('Get Device Type', bytes([0x55, 0x55, 0x40, 0x02, 0x08, 0x48, 0xAA, 0xAA])),
            ('Get Battery', bytes([0x55, 0x55, 0x40, 0x02, 0x0A, 0x4A, 0xAA, 0xAA])),
            ('Get Serial', bytes([0x55, 0x55, 0x40, 0x02, 0x0B, 0x4B, 0xAA, 0xAA])),
        ]
        
        for packet_name, packet in packets:
            logger.info(f"[{packet_name}]")
            logger.info(f"  📤 Sending: {packet.hex()}")
            
            response_received.clear()
            response_data.clear()
            
            try:
                # Write to the SAME characteristic
                await client.write_gatt_char(RW_NOTIFY_UUID, packet, response=True)
                
                # Wait for notification
                await asyncio.wait_for(response_received.wait(), timeout=3.0)
                
                if response_data:
                    data = response_data[0]
                    logger.info(f"  ✅ GOT RESPONSE!")
                    logger.info(f"     Length: {len(data)} bytes")
                    logger.info(f"     Hex: {data.hex()}")
                    
                    # Parse if it looks like NiimPrintX
                    if len(data) >= 7 and data[0:2] == b'\x55\x55' and data[-2:] == b'\xaa\xaa':
                        logger.info(f"     Header: {data[0:2].hex()} ✓")
                        logger.info(f"     Command: 0x{data[2]:02x}")
                        logger.info(f"     Length: {data[3]}")
                        logger.info(f"     Data: {data[4:-3].hex()}")
                        logger.info(f"     Checksum: 0x{data[-3]:02x}")
                        logger.info(f"     Footer: {data[-2:].hex()} ✓")
                    
                    logger.info(f"\n  🎉 THIS WORKS! Characteristic {RW_NOTIFY_UUID}")
                    break
                    
            except asyncio.TimeoutError:
                logger.info(f"  ⏱️  Timeout\n")
            except Exception as e:
                logger.info(f"  ❌ Error: {e}\n")
            
            await asyncio.sleep(0.5)
        
        await client.stop_notify(RW_NOTIFY_UUID)
        
    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_rw_notify_char())
