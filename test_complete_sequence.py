#!/usr/bin/env python3
"""Test with dimension swap and explicit feed"""

import asyncio
import sys
import os
import struct
import math
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_complete_sequence():
    """Complete print sequence matching niimprint exactly"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Create VERY simple test - just a few black lines
        width = 384
        height = 30
        
        print(f"🖼️  Creating {width}x{height}px test")
        print("   Pattern: 3 horizontal black stripes\n")
        
        # Create image with 3 black horizontal stripes
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 5, width-1, 10], fill='black')   # Stripe 1
        draw.rectangle([0, 15, width-1, 20], fill='black')  # Stripe 2
        draw.rectangle([0, 25, width-1, 28], fill='black')  # Stripe 3
        
        # Process exactly like niimprint
        img = ImageOps.invert(img.convert('L')).convert('1')
        
        print("📋 Print sequence (niimprint order):")
        print("   1. set_label_density")
        await printer.set_label_density(5)
        
        print("   2. set_label_type")
        await printer.set_label_type(1)
        
        print("   3. start_print")
        await printer.start_print()
        
        print("   4. start_page_print")
        await printer.start_page_print()
        
        print(f"   5. set_dimension({height}, {width})  ← HEIGHT, WIDTH (swapped!)")
        await printer.set_dimension(height, width)  # SWAPPED like niimprint
        
        print(f"\n📤 Sending {height} lines with headers...")
        
        for y in range(height):
            # Encode line exactly like niimprint
            line_data = [img.getpixel((x, y)) for x in range(width)]
            line_data = ''.join('0' if pix == 0 else '1' for pix in line_data)
            line_bytes = int(line_data, 2).to_bytes(math.ceil(width / 8), 'big')
            
            # Header: line_number, counts (3 zeros), flag (1)
            header = struct.pack(">H3BB", y, 0, 0, 0, 1)
            
            packet = NiimbotPacket(0x85, header + line_bytes)
            await printer._send_packet(packet, wait_response=False)
            
            if y % 10 == 0 or y == height - 1:
                print(f"   Line {y+1}/{height}")
        
        print("\n   6. end_page_print")
        await printer.end_page_print()
        
        print("   7. Sleep 0.3s")
        await asyncio.sleep(0.3)
        
        print("   8. end_print (with retry loop)")
        for attempt in range(10):
            result = await printer.end_print()
            if result:
                print(f"      ✅ Success on attempt {attempt + 1}")
                break
            print(f"      ⏳ Retry {attempt + 1}/10...")
            await asyncio.sleep(0.1)
        
        print("\n✅ Sequence complete!")
        print("\n🔍 Did it:")
        print("   1. Feed a label? (YES/NO)")
        print("   2. Print black stripes? (YES/NO)")
        print("   3. Print blank? (YES/NO)")
        print("   4. Nothing at all? (YES/NO)")

if __name__ == "__main__":
    asyncio.run(test_complete_sequence())
