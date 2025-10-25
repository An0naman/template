#!/usr/bin/env python3
"""Test if printer requires button press or additional command"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_print_trigger():
    """Test various commands that might trigger physical printing"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Send VERY simple data first
        width = 384
        height = 10
        img = Image.new('1', (width, height), 1)
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 2, 284, 8], fill=0)  # Simple black rectangle
        
        print("🖼️  Preparing tiny test label (384x10px)")
        
        # Standard print sequence
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        # Send data
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
        await printer.end_print()
        
        print("✅ Data sent\n")
        
        # Now try various trigger commands
        print("🧪 Trying potential print trigger commands...\n")
        
        commands_to_try = [
            (0xF1, b'', "Feed/Print (0xF1)"),
            (0x66, b'\x01', "Print trigger (0x66)"),
            (0xA4, b'', "Unknown (0xA4)"),
            (0xA6, b'', "Unknown (0xA6)"),
            (0x20, b'\x01', "Allow print with data"),
        ]
        
        for cmd, data, desc in commands_to_try:
            print(f"   Sending {desc}...")
            packet = NiimbotPacket(cmd, data)
            result = await printer._send_packet(packet)
            if result:
                print(f"   ✅ Response: type=0x{result.type:02x}, data={result.data.hex()}")
            else:
                print(f"   ⏱️  No response (timeout)")
            await asyncio.sleep(0.5)
        
        print("\n" + "="*60)
        print("📋 INSTRUCTIONS:")
        print("="*60)
        print("1. Check if anything printed after the commands above")
        print("2. If not, try PRESSING THE BUTTON on your B1 printer")
        print("3. The data may already be in the printer's buffer")
        print("4. Report back what happens!")
        print("="*60)
        
        # Keep connection alive for 30 seconds to allow button press
        print("\n⏳ Keeping connection alive for 30 seconds...")
        print("   Try pressing the print button on your printer now...")
        
        for i in range(30):
            await asyncio.sleep(1)
            if i % 5 == 0:
                # Send heartbeat to keep connection alive
                await printer.send_heartbeat()
                print(f"   {30-i} seconds remaining...")

if __name__ == "__main__":
    asyncio.run(test_print_trigger())
