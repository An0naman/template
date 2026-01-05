#!/usr/bin/env python3
"""Test BLE with correct packet headers from niimprint library"""

import asyncio
import sys
import os
import struct
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_with_headers():
    """Send image data with proper headers like niimprint does"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Create test image - solid black rectangle
        width = 384
        height = 50
        
        print(f"🖼️  Creating {width}x{height}px test image")
        print("   Pattern: Black rectangle in center\n")
        
        img = Image.new('RGB', (width, height), 'white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 10, 334, 40], fill='black')
        
        # Process image like niimprint does
        print("📐 Processing image (niimprint style):")
        print("   1. Convert to L (grayscale)")
        print("   2. Invert colors")
        print("   3. Convert to 1-bit (black & white)")
        
        img = ImageOps.invert(img.convert('L')).convert('1')
        
        print("\n📋 Starting print sequence...")
        await printer.set_label_density(5)  # Max density
        await printer.set_label_type(1)
        await printer.start_print()
        await printer.start_page_print()
        await printer.set_dimension(height, width)  # Note: niimprint swaps these!
        
        print(f"\n📤 Sending {height} lines with headers...")
        
        for y in range(height):
            # Build line data
            line_data = []
            for x in range(width):
                pixel = img.getpixel((x, y))
                line_data.append('0' if pixel == 0 else '1')
            
            # Convert to bytes (exactly like niimprint)
            line_bits = ''.join(line_data)
            line_bytes = int(line_bits, 2).to_bytes((width + 7) // 8, 'big')
            
            # Create header: line_number (2 bytes) + counts (3 bytes) + flag (1 byte)
            # niimprint sends: struct.pack(">H3BB", y, 0, 0, 0, 1)
            header = struct.pack(">H3BB", y, 0, 0, 0, 1)
            
            # Combine header + line data
            packet_data = header + line_bytes
            
            # Send as command 0x85
            packet = NiimbotPacket(0x85, packet_data)
            await printer._send_packet(packet, wait_response=False)
            
            if y % 10 == 0 or y == height - 1:
                print(f"   Line {y+1}/{height}: header={header.hex()}, data={len(line_bytes)} bytes")
        
        print("\n📋 Finishing...")
        await printer.end_page_print()
        
        # Wait and retry end_print like niimprint does
        await asyncio.sleep(0.3)
        print("   Calling end_print (with retries)...")
        
        for attempt in range(5):
            result = await printer.end_print()
            if result:
                print(f"   ✅ end_print succeeded on attempt {attempt + 1}")
                break
            print(f"   ⏳ end_print returned false, retry {attempt + 1}/5...")
            await asyncio.sleep(0.1)
        
        print("\n✅ Print sequence complete!")
        print("   Check if label printed automatically (should have black rectangle)")

if __name__ == "__main__":
    asyncio.run(test_with_headers())
