#!/usr/bin/env python3
"""Test with reversed bit order"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_bit_order():
    """Test different bit ordering"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Very simple: 384x20px, just horizontal stripes
        width = 384
        height = 20
        
        img = Image.new('1', (width, height), 1)  # White background
        draw = ImageDraw.Draw(img)
        # Draw alternating black/white horizontal stripes (easy to debug)
        for y in range(height):
            if y % 4 < 2:  # Every other 2 lines
                draw.line([(0, y), (width-1, y)], fill=0)
        
        print("🖼️  Test image: horizontal stripes")
        print(f"    Size: {width}x{height}px\n")
        
        # Setup
        await printer.start_print()
        await printer.set_label_type(1)
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        # Try NORMAL bit order (MSB first, black = 1)
        print("📤 Test 1: Normal bit order (MSB first, black=1)...")
        for y in range(height):
            line_data = []
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel = img.getpixel((x + bit, y))
                        if pixel == 0:  # Black
                            byte |= (1 << (7 - bit))  # MSB first
                line_data.append(byte)
            
            packet = NiimbotPacket(0x85, bytes(line_data))
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Sent with normal bit order\n")
        await asyncio.sleep(2)
        
        # Try again with LSB first
        print("📤 Test 2: Reversed bit order (LSB first, black=1)...")
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        for y in range(height):
            line_data = []
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel = img.getpixel((x + bit, y))
                        if pixel == 0:  # Black
                            byte |= (1 << bit)  # LSB first
                line_data.append(byte)
            
            packet = NiimbotPacket(0x85, bytes(line_data))
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Sent with reversed bit order\n")
        await asyncio.sleep(2)
        
        # Try with inverted pixels (white=1, black=0)
        print("📤 Test 3: Inverted pixels (white=1, black=0, MSB first)...")
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        for y in range(height):
            line_data = []
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel = img.getpixel((x + bit, y))
                        if pixel == 1:  # WHITE
                            byte |= (1 << (7 - bit))  # MSB first
                line_data.append(byte)
            
            packet = NiimbotPacket(0x85, bytes(line_data))
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Sent with inverted pixels\n")
        
        print("\n🎯 All 3 tests sent. Check if any printed correctly!")
        print("   Test 1: Normal (MSB, black=1)")
        print("   Test 2: LSB first (black=1)")
        print("   Test 3: Inverted (MSB, white=1)")

if __name__ == "__main__":
    asyncio.run(test_bit_order())
