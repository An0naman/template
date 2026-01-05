#!/usr/bin/env python3
"""Test the updated niimbot_printer_ble service with B1"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

async def test_b1_print():
    """Test B1 printing with updated service"""
    
    # Create test image
    width = 384
    height = 50
    
    print(f"🖼️  Creating {width}x{height}px test image")
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 10, 334, 40], fill='black')
    draw.text((width//2, 25), "TEST PRINT", fill='white', anchor='mm')
    
    # Connect and print
    async with NiimbotPrinterBLE("B1", model="b1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected to B1\n")
        
        # Print image
        print("🖨️  Starting print...")
        success = await printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("\n✅ Print completed successfully!")
        else:
            print("\n❌ Print failed")

if __name__ == "__main__":
    asyncio.run(test_b1_print())
