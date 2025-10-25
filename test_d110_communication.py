#!/usr/bin/env python3
"""
Test D110 printer communication
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# D110 Address
PRINTER_ADDRESS = "C3:33:D5:02:36:62"


async def test_d110():
    """Test D110 printer"""
    logger.info("=" * 70)
    logger.info("TESTING NIIMBOT D110")
    logger.info(f"Address: {PRINTER_ADDRESS}")
    logger.info("=" * 70)
    
    async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
        if not client.is_connected:
            logger.error("❌ Failed to connect!")
            return
        
        logger.info("\n✅ Connected successfully!\n")
        
        # Show GATT services
        logger.info("📋 GATT Services:")
        logger.info("-" * 70)
        
        write_chars = []
        notify_chars = []
        
        for service in client.services:
            logger.info(f"\n🔧 Service: {service.uuid}")
            
            for char in service.characteristics:
                props = ', '.join(char.properties)
                logger.info(f"   📝 {char.uuid}")
                logger.info(f"      Properties: {props}")
                
                if 'write' in char.properties:
                    write_chars.append(char.uuid)
                if 'notify' in char.properties:
                    notify_chars.append(char.uuid)
        
        logger.info("\n" + "=" * 70)
        logger.info("TESTING COMMUNICATION")
        logger.info("=" * 70)
        
        if not write_chars or not notify_chars:
            logger.error("❌ No suitable write/notify characteristics found!")
            return
        
        # Try each combination
        test_packet = bytes([0x55, 0x55, 0xDC, 0x02, 0x01, 0xDD, 0xAA, 0xAA])
        
        for notify_uuid in notify_chars:
            response_received = asyncio.Event()
            response_data = []
            
            def notification_handler(sender, data):
                logger.info(f"      📨 RESPONSE: {data.hex()}")
                response_data.append(data)
                response_received.set()
            
            try:
                await client.start_notify(notify_uuid, notification_handler)
                logger.info(f"\n✓ Monitoring: {notify_uuid}")
                
                for write_uuid in write_chars:
                    logger.info(f"\n   Trying write to: {write_uuid}")
                    logger.info(f"   📤 Sending heartbeat: {test_packet.hex()}")
                    
                    response_received.clear()
                    response_data.clear()
                    
                    try:
                        await client.write_gatt_char(write_uuid, test_packet)
                        await asyncio.wait_for(response_received.wait(), timeout=2.0)
                        
                        if response_data:
                            logger.info(f"\n   🎉 SUCCESS!")
                            logger.info(f"      Write UUID: {write_uuid}")
                            logger.info(f"      Notify UUID: {notify_uuid}")
                            logger.info(f"      Response: {response_data[0].hex()}")
                            
                            await client.stop_notify(notify_uuid)
                            return write_uuid, notify_uuid
                            
                    except asyncio.TimeoutError:
                        logger.info(f"      ⏱️  No response")
                    except Exception as e:
                        logger.info(f"      ❌ Error: {e}")
                    
                    await asyncio.sleep(0.3)
                
                await client.stop_notify(notify_uuid)
                
            except Exception as e:
                logger.info(f"   ❌ Error setting up notifications: {e}")
        
        logger.info("\n❌ No working combination found")
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_d110())
