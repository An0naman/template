#!/usr/bin/env python3
"""Debug print sequence to see what commands succeed"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def debug_print_sequence():
    """Test each step of the print sequence"""
    
    # Create a tiny test image (just 10 lines)
    width = 384
    height = 10
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=1)
    
    # Convert to 1-bit
    from PIL import ImageOps
    img = ImageOps.invert(img.convert('L')).convert('1')
    
    print("Connecting to B1...")
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Test each command
        print("1. Heartbeat...")
        result = await printer.send_heartbeat()
        print(f"   {'✅' if result else '❌'} Result: {result.data.hex() if result else 'None'}\n")
        
        print("2. Start print...")
        result = await printer.start_print()
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("3. Set density (3)...")
        result = await printer.set_label_density(3)
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("4. Set dimensions (384x10)...")
        result = await printer.set_dimension(width, height)
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("5. Set quantity (1)...")
        result = await printer.set_quantity(1)
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("6. Start page...")
        result = await printer.start_page_print()
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("7. Sending 10 lines of image data...")
        for y in range(height):
            line_data = []
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel = img.getpixel((x + bit, y))
                        if pixel == 0:
                            byte |= (1 << (7 - bit))
                line_data.append(byte)
            
            packet = NiimbotPacket(0x85, bytes(line_data))
            await printer._send_packet(packet, wait_response=False)
            print(f"   Line {y+1}/{height} sent ({len(line_data)} bytes)")
        
        print("\n8. End page...")
        result = await printer.end_page_print()
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("9. End print...")
        result = await printer.end_print()
        print(f"   {'✅' if result else '❌'} Result: {result}\n")
        
        print("10. Checking print status...")
        status = await printer.get_print_status()
        print(f"   Status: {status}\n")
        
        print("\n🎯 All commands sent. Check if label printed.")
        print("If nothing printed, the printer might need:")
        print("  - A 'feed' or 'eject' command")
        print("  - Different packet structure")
        print("  - Additional initialization")

if __name__ == "__main__":
    asyncio.run(debug_print_sequence())
