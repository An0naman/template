#!/usr/bin/env python3
"""
Scan for BOTH Niimbot printers and identify them
"""

import asyncio
import logging
from bleak import BleakScanner

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def scan_for_printers():
    """Scan for all Niimbot printers"""
    logger.info("=" * 70)
    logger.info("SCANNING FOR NIIMBOT PRINTERS")
    logger.info("=" * 70)
    logger.info("\nScanning for 10 seconds...\n")
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    niimbot_devices = []
    
    for device in devices:
        if device.name and ('niimbot' in device.name.lower() or 
                           'b1' in device.name.lower() or 
                           'd110' in device.name.lower() or
                           'd11' in device.name.lower()):
            niimbot_devices.append(device)
            logger.info(f"📱 Found: {device.name}")
            logger.info(f"   Address: {device.address}")
            if hasattr(device, 'rssi'):
                logger.info(f"   Signal: {device.rssi} dBm")
            logger.info("")
    
    if not niimbot_devices:
        logger.info("❌ No Niimbot printers found")
        logger.info("\nMake sure:")
        logger.info("  1. Printer is turned on")
        logger.info("  2. Printer is in pairing mode (blue light)")
        logger.info("  3. Printer is not connected to phone app")
    else:
        logger.info("=" * 70)
        logger.info(f"FOUND {len(niimbot_devices)} NIIMBOT PRINTER(S)")
        logger.info("=" * 70)
        
        for i, device in enumerate(niimbot_devices, 1):
            logger.info(f"\n[{i}] {device.name}")
            logger.info(f"    Address: {device.address}")
            
            # Identify model
            if 'b1' in device.name.lower():
                logger.info(f"    Model: B1 (thermal label printer)")
            elif 'd110' in device.name.lower() or 'd11' in device.name.lower():
                logger.info(f"    Model: D110 (thermal label printer)")
            else:
                logger.info(f"    Model: Unknown")
    
    return niimbot_devices


if __name__ == "__main__":
    devices = asyncio.run(scan_for_printers())
