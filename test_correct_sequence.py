#!/usr/bin/env python3
"""Test with allow_print_clear BEFORE start_page and proper counts"""

import asyncio
import sys
import os
import struct
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

def count_bits(data):
    """Count number of 1 bits in bytes"""
    return int.from_bytes(data, 'big').bit_count()

async def test_correct_sequence():
    """Test with correct sequence from original niimprint"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Create test image - just black rectangle
        width = 384  # B1 width
        height = 40
        
        print(f"🖼️  Creating {width}x{height}px test")
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 10, 334, 30], fill='black')
        draw.text((width//2, height//2), "NIIMBOT", fill='black', anchor='mm')
        
        # Process like niimprint
        img_data = ImageOps.invert(img.convert('L')).convert('1')
        
        print("\n📋 Print sequence (CORRECT ORDER from niimprint):")
        print("   1. set_label_type")
        await printer.set_label_type(1)
        
        print("   2. set_label_density")
        await printer.set_label_density(3)
        
        print("   3. start_print")
        await printer.start_print()
        
        print("   4. allow_print_clear ← BEFORE start_page!")
        packet = NiimbotPacket(0x20, b'\x01')
        await printer._send_packet(packet)
        
        print("   5. start_page_print")
        await printer.start_page_print()
        
        print(f"   6. set_dimension({height}, {width})")
        await printer.set_dimension(height, width)
        
        print(f"   7. set_quantity(1)")
        await printer.set_quantity(1)
        
        print(f"\n📤 Sending {height} lines with PROPER COUNTS...")
        
        bytes_per_line = 48  # 384 pixels / 8
        
        for y in range(height):
            # Get line data
            line_bytes = bytearray()
            for x in range(width):
                if x % 8 == 0:
                    line_bytes.append(0)
                pixel = img_data.getpixel((x, y))
                if pixel == 0:  # Black
                    line_bytes[-1] |= (1 << (7 - (x % 8)))
            
            # Calculate bit counts for 3 segments (like niimprint)
            segment_size = bytes_per_line // 3
            count1 = count_bits(bytes(line_bytes[0:segment_size]))
            count2 = count_bits(bytes(line_bytes[segment_size:segment_size*2]))
            count3 = count_bits(bytes(line_bytes[segment_size*2:]))
            
            # Build header with counts
            header = struct.pack(">H3BB", y, count1, count2, count3, 1)
            
            # Send packet
            packet = NiimbotPacket(0x85, header + bytes(line_bytes))
            await printer._send_packet(packet, wait_response=False)
            
            if y == 0 or y == height - 1:
                print(f"   Line {y}: counts=({count1}, {count2}, {count3})")
        
        print("\n   8. end_page_print")
        await printer.end_page_print()
        
        print("   9. Checking print status...")
        for i in range(10):
            status = await printer.get_print_status()
            print(f"      Status: {status}")
            if status == 1:  # Assuming 1 means done
                break
            await asyncio.sleep(0.1)
        
        print("   10. end_print")
        await printer.end_print()
        
        print("\n✅ Complete! Did it print with text?")

if __name__ == "__main__":
    asyncio.run(test_correct_sequence())
