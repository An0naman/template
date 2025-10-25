#!/usr/bin/env python3
"""Send print job via BLE and wait for button press"""

import asyncio
import sys
import os
import struct
import math
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_with_button():
    """Send complete print job, then wait for user to press printer button"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Create simple test
        width = 384
        height = 40
        
        print(f"🖼️  Creating {width}x{height}px test label")
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw "PRESS BUTTON" text and box
        draw.rectangle([10, 5, width-10, height-5], outline='black', width=4)
        draw.text((width//2, height//2), "PRESS BUTTON TO PRINT", fill='black', anchor='mm')
        
        # Process
        img = ImageOps.invert(img.convert('L')).convert('1')
        
        print("📤 Sending print job...")
        await printer.set_label_density(5)
        await printer.set_label_type(1)
        await printer.start_print()
        await printer.start_page_print()
        await printer.set_dimension(height, width)
        
        # Send image data
        for y in range(height):
            line_data = [img.getpixel((x, y)) for x in range(width)]
            line_data = ''.join('0' if pix == 0 else '1' for pix in line_data)
            line_bytes = int(line_data, 2).to_bytes(math.ceil(width / 8), 'big')
            header = struct.pack(">H3BB", y, 0, 0, 0, 1)
            packet = NiimbotPacket(0x85, header + line_bytes)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await asyncio.sleep(0.3)
        
        for _ in range(10):
            if await printer.end_print():
                break
            await asyncio.sleep(0.1)
        
        print("✅ Print job sent to printer!\n")
        print("="*60)
        print("🔘 NOW PRESS THE BUTTON ON YOUR B1 PRINTER")
        print("="*60)
        print("\n⏳ Waiting 30 seconds...")
        print("   (keeping connection alive)")
        
        for i in range(30):
            await asyncio.sleep(1)
            if i % 5 == 0:
                await printer.send_heartbeat()
                print(f"   {30-i}s remaining...")
        
        print("\n📋 Result: Did pressing the button print the label? (YES/NO)")

if __name__ == "__main__":
    asyncio.run(test_with_button())
