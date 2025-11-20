#!/usr/bin/env python3
"""Test additional commands that might trigger printing"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_print_with_variations():
    """Test print with different command variations"""
    
    # Create tiny test image
    width = 384
    height = 10
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 2, width-10, height-2], fill='black')
    img = ImageOps.invert(img.convert('L')).convert('1')
    
    print("Testing print sequence variations...\n")
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Standard sequence
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        
        # Try ALLOW_PRINT_CLEAR before starting page
        print("🧪 Sending ALLOW_PRINT_CLEAR (0x20) before page...")
        packet = NiimbotPacket(0x20, b'')
        result = await printer._send_packet(packet)
        print(f"   Result: {result}\n")
        
        await printer.start_page_print()
        
        # Send image data
        print("📤 Sending image data...")
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
        
        await printer.end_page_print()
        
        # Try ALLOW_PRINT_CLEAR after page
        print("\n🧪 Sending ALLOW_PRINT_CLEAR (0x20) after page...")
        packet = NiimbotPacket(0x20, b'')
        result = await printer._send_packet(packet)
        print(f"   Result: {result}\n")
        
        await printer.end_print()
        
        # Check status
        print("📊 Checking status...")
        status = await printer.get_print_status()
        print(f"   Print status: {status}\n")
        
        # Try a few more potential commands
        print("🧪 Trying command 0x19 (SET_DIMENSION alternative)...")
        packet = NiimbotPacket(0x19, bytes([0x01, 0x80, 0x00, 0x0A]))  # width=384, height=10
        result = await printer._send_packet(packet)
        print(f"   Result: {result}\n")
        
        print("🧪 Trying command 0x70 (possible feed/eject)...")
        packet = NiimbotPacket(0x70, b'')
        result = await printer._send_packet(packet)
        print(f"   Result: {result}\n")
        
        print("🧪 Trying command 0x71...")
        packet = NiimbotPacket(0x71, b'')
        result = await printer._send_packet(packet)
        print(f"   Result: {result}\n")
        
        await asyncio.sleep(2)
        
        print("\n✅ Test complete. Did anything print?")

if __name__ == "__main__":
    asyncio.run(test_print_with_variations())
