#!/usr/bin/env python3
"""Test with RFID-detected label parameters"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_with_rfid_params():
    """Use RFID-detected label type and parameters"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Get RFID info first
        print("📡 Reading RFID...")
        rfid = await printer.get_rfid()
        if rfid:
            print(f"   Barcode: {rfid.get('barcode')}")
            print(f"   Type: {rfid.get('type')}")
            print(f"   Data: {rfid}\n")
            
            label_type = rfid.get('type', 1)
        else:
            print("   No RFID, using type 1\n")
            label_type = 1
        
        # Create very simple image - just a black rectangle
        # B1 spec: 384 pixels width (32mm at 12 pixels/mm)
        width = 384
        height = 50  # Very short label for testing
        
        print(f"🖼️  Creating {width}x{height}px test image...")
        img = Image.new('1', (width, height), 1)  # Start with white (1)
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 10, 334, 40], fill=0)  # Black rectangle
        
        print("📋 Print sequence:")
        print("   1. Start print...")
        if not await printer.start_print():
            print("   ❌ Failed"); return
        print("   ✅")
        
        print(f"   2. Set label type ({label_type})...")
        if not await printer.set_label_type(label_type):
            print("   ❌ Failed"); return
        print("   ✅")
        
        print("   3. Set density (3)...")
        if not await printer.set_label_density(3):
            print("   ❌ Failed"); return
        print("   ✅")
        
        print(f"   4. Set dimension ({width}x{height})...")
        if not await printer.set_dimension(width, height):
            print("   ❌ Failed"); return
        print("   ✅")
        
        print("   5. Set quantity (1)...")
        if not await printer.set_quantity(1):
            print("   ❌ Failed"); return
        print("   ✅")
        
        print("   6. Start page...")
        if not await printer.start_page_print():
            print("   ❌ Failed"); return
        print("   ✅")
        
        print(f"   7. Send {height} lines of image data...")
        for y in range(height):
            line_data = []
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        pixel = img.getpixel((x + bit, y))
                        if pixel == 1:  # White pixel (inverted logic)
                            byte |= (1 << (7 - bit))
                line_data.append(byte)
            
            packet = NiimbotPacket(0x85, bytes(line_data))
            await printer._send_packet(packet, wait_response=False)
            
            if y % 10 == 0 or y == height-1:
                print(f"      {y+1}/{height} lines sent")
        print("   ✅")
        
        print("   8. End page...")
        if not await printer.end_page_print():
            print("   ❌ Failed"); return
        print("   ✅")
        
        print("   9. Allow print clear...")
        packet = NiimbotPacket(0x20, b'')
        await printer._send_packet(packet)
        print("   ✅")
        
        print("   10. End print...")
        if not await printer.end_print():
            print("   ❌ Failed"); return
        print("   ✅")
        
        await asyncio.sleep(1)
        
        print("\n✅ Complete! Check printer for output.")
        print("\n💡 If still nothing prints, the issue may be:")
        print("   - Image encoding (bit order)")
        print("   - Missing printer-specific initialization")
        print("   - Printer needs button press to print")
        print("   - Different protocol version for this model")

if __name__ == "__main__":
    asyncio.run(test_with_rfid_params())
