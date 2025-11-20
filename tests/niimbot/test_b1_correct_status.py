#!/usr/bin/env python3
"""Test with EXACT B1 sequence: status polling instead of PrintEnd payload"""

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

async def test_b1_correct_sequence():
    """Test with EXACT B1 sequence from niimbluelib"""
    
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
        density = 3  # Default
        labelType = 1  # With gaps
        
        print("\n📋 EXACT B1 Print Sequence from niimbluelib:")
        
        # ==================== INIT ====================
        print("\n🔧 printInit():")
        
        print("   SetDensity(3)")
        packet = NiimbotPacket(0x21, bytes([density]))
        await printer._send_packet(packet)
        
        print("   SetLabelType(1)")
        packet = NiimbotPacket(0x23, bytes([labelType]))
        await printer._send_packet(packet)
        
        print(f"   PrintStart7b [totalPages(u16), 0x00, 0x00, 0x00, 0x00, pageColor(u8)]")
        # Pack: totalPages as u16 (2 bytes) + 4 zeros + pageColor
        data = struct.pack(">H5B", totalPages, 0, 0, 0, 0, pageColor)
        print(f"      Data: {data.hex()} ({len(data)} bytes)")
        packet = NiimbotPacket(0x01, data)
        await printer._send_packet(packet)
        
        # ==================== PAGE ====================
        print("\n📄 printPage():")
        
        print("   PageStart")
        packet = NiimbotPacket(0x03, b'\x01')
        await printer._send_packet(packet)
        
        print(f"   SetPageSize6b [rows(u16), cols(u16), copiesCount(u16)]")
        # Pack: height, width, quantity (all as u16)
        data = struct.pack(">HHH", height, width, 1)
        print(f"      Data: {data.hex()} = rows={height}, cols={width}, copies=1")
        packet = NiimbotPacket(0x13, data)
        await printer._send_packet(packet)
        
        print(f"   Sending {height} bitmap rows...")
        bytes_per_line = width // 8
        
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
            # For 384px = 48 bytes, split as 16+16+16
            seg_size = bytes_per_line // 3
            
            count1 = count_bits(bytes(line_bytes[0:seg_size]))
            count2 = count_bits(bytes(line_bytes[seg_size:seg_size*2]))
            count3 = count_bits(bytes(line_bytes[seg_size*2:]))
            
            # Build header: pos(u16), count1(u8), count2(u8), count3(u8), repeats(u8)
            header = struct.pack(">H3BB", y, count1, count2, count3, 1)
            
            # Send
            packet = NiimbotPacket(0x85, header + bytes(line_bytes))
            await printer._send_packet(packet, wait_response=False)
            
            if y % 10 == 0:
                print(f"      Row {y}: counts=({count1}, {count2}, {count3})")
        
        print(f"   PageEnd")
        packet = NiimbotPacket(0xE3, b'\x01')
        await printer._send_packet(packet)
        
        # ==================== WAIT FOR FINISHED ====================
        print("\n⏳ waitForFinished() - Status polling:")
        
        timeout_seconds = 5
        poll_interval = 0.3
        polls = int(timeout_seconds / poll_interval)
        
        for i in range(polls):
            # PrintStatus command (0xA3) NOT PrintEnd!
            packet = NiimbotPacket(0xA3, b'')
            resp = await printer._send_packet(packet)
            
            if resp and len(resp.data) >= 4:
                # Parse: page(i16), pagePrintProgress(i8), pageFeedProgress(i8)
                page = struct.unpack(">h", resp.data[0:2])[0]
                print_progress = resp.data[2]
                feed_progress = resp.data[3]
                
                print(f"   Poll {i+1}: page={page}/{totalPages}, print={print_progress}%, feed={feed_progress}%")
                
                if page == totalPages and print_progress == 100 and feed_progress == 100:
                    print(f"   ✅ Print complete!")
                    break
            
            await asyncio.sleep(poll_interval)
        
        # ==================== END ====================
        print("\n🏁 printEnd():")
        print("   PrintEnd (NO payload)")
        packet = NiimbotPacket(0xF3, b'')  # NO DATA!
        result = await printer._send_packet(packet)
        
        if result:
            success = result.data[0] == 1 if len(result.data) > 0 else False
            print(f"      Response: {result.data.hex()}")
            print(f"      Success: {success}")
        
        print("\n✅ EXACT B1 sequence complete!")
        print("   Did it print now?")

if __name__ == "__main__":
    asyncio.run(test_b1_correct_sequence())
