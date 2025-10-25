#!/usr/bin/env python3
"""Test with correct B1-specific sequence from niimbluelib"""

import asyncio
import sys
import os
import struct
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

def count_bits(data):
    """Count number of 1 bits"""
    return int.from_bytes(data, 'big').bit_count()

async def test_b1_sequence():
    """Test with B1-specific sequence"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        # Create test image
        width = 384
        height = 50
        
        print(f"🖼️  Creating {width}x{height}px test")
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 10, 334, 40], fill='black')
        draw.text((width//2, 25), "NIIMBOT B1", fill='white', anchor='mm')
        
        # Process
        img_data = ImageOps.invert(img.convert('L')).convert('1')
        
        totalPages = 1
        pageColor = 0
        
        print("\n📋 B1-specific Print Sequence:")
        
        # Init
        print("   1. SetDensity(5)")
        packet = NiimbotPacket(0x21, bytes([5]))
        await printer._send_packet(packet)
        
        print("   2. SetLabelType(1)")
        packet = NiimbotPacket(0x23, bytes([1]))
        await printer._send_packet(packet)
        
        print(f"   3. PrintStart [totalPages(u16), 0, 0, 0, 0, pageColor(u8)] ← 7 BYTES!")
        # Pack: totalPages as u16 (2 bytes) + 4 zeros + pageColor
        data = struct.pack(">H", totalPages) + bytes([0, 0, 0, 0, pageColor])
        print(f"      Data: {data.hex()} ({len(data)} bytes)")
        packet = NiimbotPacket(0x01, data)
        await printer._send_packet(packet)
        
        # Page
        print("\n   4. PageStart")
        packet = NiimbotPacket(0x03, b'\x01')
        await printer._send_packet(packet)
        
        print(f"   5. SetPageSize [rows(u16), cols(u16), copiesCount(u16)] ← 6 BYTES!")
        # Pack: height, width, quantity (all as u16)
        data = struct.pack(">HHH", height, width, 1)
        print(f"      Data: {data.hex()} = height={height}, width={width}, copies=1")
        packet = NiimbotPacket(0x13, data)
        await printer._send_packet(packet)
        
        print(f"\n   6. Sending {height} bitmap rows...")
        bytes_per_line = 48
        
        for y in range(height):
            # Get line data
            line_bytes = bytearray()
            for x in range(width):
                if x % 8 == 0:
                    line_bytes.append(0)
                pixel = img_data.getpixel((x, y))
                if pixel == 0:
                    line_bytes[-1] |= (1 << (7 - (x % 8)))
            
            # Calculate bit counts for 3 segments
            seg_size = bytes_per_line // 3
            count1 = count_bits(bytes(line_bytes[0:seg_size]))
            count2 = count_bits(bytes(line_bytes[seg_size:seg_size*2]))
            count3 = count_bits(bytes(line_bytes[seg_size*2:]))
            
            # Build header
            header = struct.pack(">H3BB", y, count1, count2, count3, 1)
            
            # Send
            packet = NiimbotPacket(0x85, header + bytes(line_bytes))
            await printer._send_packet(packet, wait_response=False)
            
            if y == 0 or y == height - 1:
                print(f"      Row {y}: counts=({count1}, {count2}, {count3})")
        
        print("\n   7. PageEnd")
        packet = NiimbotPacket(0xE3, b'\x01')
        await printer._send_packet(packet)
        
        print("   8. Status poll...")
        for i in range(5):
            status = await printer.get_print_status()
            print(f"      Status: {status}")
            if status == totalPages:
                break
            await asyncio.sleep(0.2)
        
        print("   9. PrintEnd")
        packet = NiimbotPacket(0xF3, b'\x01')
        result = await printer._send_packet(packet)
        print(f"      Result: {result.data.hex() if result else 'None'}")
        
        print("\n✅ Sequence complete!")
        print("   Did it print?")

if __name__ == "__main__":
    asyncio.run(test_b1_sequence())
