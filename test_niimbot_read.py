#!/usr/bin/env python3
"""
Read all readable characteristics from B1
"""

import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PRINTER_ADDRESS = "13:07:12:A6:40:07"


async def read_all_chars():
    """Read all readable characteristics"""
    logger.info("=" * 70)
    logger.info("READING ALL CHARACTERISTICS")
    logger.info("=" * 70)
    
    async with BleakClient(PRINTER_ADDRESS, timeout=30.0) as client:
        if not client.is_connected:
            logger.error("❌ Failed to connect!")
            return
        
        logger.info("✅ Connected\n")
        
        for service in client.services:
            logger.info(f"\n🔧 Service: {service.uuid}")
            
            for char in service.characteristics:
                logger.info(f"\n   📝 {char.uuid}")
                logger.info(f"      Properties: {', '.join(char.properties)}")
                
                # Try to read if readable
                if 'read' in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        logger.info(f"      ✓ Value ({len(value)} bytes): {value.hex()}")
                        
                        # Try to decode if printable
                        try:
                            text = value.decode('utf-8', errors='ignore')
                            if text.isprintable():
                                logger.info(f"      ✓ Text: {text}")
                        except:
                            pass
                    except Exception as e:
                        logger.info(f"      ✗ Error reading: {e}")
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(read_all_chars())
