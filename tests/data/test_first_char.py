#!/usr/bin/env python3
"""Test with the FIRST characteristic found on B1"""

import asyncio
import sys
import os
import struct
import math
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageOps
from bleak import BleakClient

# Use the FIRST characteristic we found
CHAR_UUID = "49535343-aca3-481c-91ec-d85e28a60318"  # From service 49535343-fe7d-...

class NiimbotPacket:
    def __init__(self, type_, data=b""):
        self.type = type_
        self.data = data
    
    def to_bytes(self):
        checksum = self.type ^ len(self.data)
        for i in self.data:
            checksum ^= i
        return bytes([0x55, 0x55, self.type, len(self.data), *self.data, checksum, 0xAA, 0xAA])

async def test_first_char():
    """Test with first characteristic"""
    
    address = "13:07:12:A6:40:07"
    
    print(f"Connecting to B1 at {address}...")
    print(f"Using characteristic: {CHAR_UUID}\n")
    
    async with BleakClient(address) as client:
        print("✅ Connected!")
        
        # Start notifications
        responses = []
        def handler(sender, data):
            responses.append(data)
            print(f"📨 Response: {data.hex()}")
        
        await client.start_notify(CHAR_UUID, handler)
        print("✓ Notifications started\n")
        
        # Create simple test image
        width = 384
        height = 30
        
        print("🖼️  Creating test image with thick black stripe")
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 10, width-1, 20], fill='black')
        
        # Process
        img = ImageOps.invert(img.convert('L')).convert('1')
        
        print("\n📋 Sending print sequence...")
        
        # Send commands
        commands = [
            (0x21, bytes([5]), "set_density(5)"),
            (0x23, bytes([1]), "set_label_type(1)"),
            (0x01, b'\x01', "start_print"),
            (0x03, b'\x01', "start_page"),
            (0x13, struct.pack(">HH", height, width), f"set_dimension({height}, {width})"),
        ]
        
        for cmd, data, desc in commands:
            packet = NiimbotPacket(cmd, data)
            print(f"   {desc}...")
            await client.write_gatt_char(CHAR_UUID, packet.to_bytes())
            await asyncio.sleep(0.1)
        
        print(f"\n📤 Sending {height} lines...")
        for y in range(height):
            line_data = [img.getpixel((x, y)) for x in range(width)]
            line_data = ''.join('0' if pix == 0 else '1' for pix in line_data)
            line_bytes = int(line_data, 2).to_bytes(math.ceil(width / 8), 'big')
            header = struct.pack(">H3BB", y, 0, 0, 0, 1)
            packet = NiimbotPacket(0x85, header + line_bytes)
            await client.write_gatt_char(CHAR_UUID, packet.to_bytes(), response=False)
            
            if y % 10 == 0:
                print(f"   Line {y+1}/{height}")
        
        print("\n📋 Finishing...")
        end_commands = [
            (0xE3, b'\x01', "end_page"),
            (0xF3, b'\x01', "end_print"),
        ]
        
        for cmd, data, desc in end_commands:
            packet = NiimbotPacket(cmd, data)
            print(f"   {desc}...")
            await client.write_gatt_char(CHAR_UUID, packet.to_bytes())
            await asyncio.sleep(0.2)
        
        await asyncio.sleep(2)
        
        print("\n✅ Sequence complete!")
        print("   Did it print automatically? (with black stripe)")

if __name__ == "__main__":
    asyncio.run(test_first_char())
