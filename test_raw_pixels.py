#!/usr/bin/env python3
"""Test with manual pixel data to find correct encoding"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_raw_pixels():
    """Send known pixel patterns to determine correct encoding"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        width = 384  # 384 pixels = 48 bytes per line
        height = 20
        
        print("🧪 Test 1: All BLACK pixels (all 0xFF bytes)")
        print("   Expected: Solid black rectangle\n")
        
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        # Send all black (0xFF = all bits set)
        for y in range(height):
            line_data = bytes([0xFF] * 48)  # 384 pixels / 8 = 48 bytes
            packet = NiimbotPacket(0x85, line_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Test 1 sent (all black)\n")
        await asyncio.sleep(2)
        
        print("🧪 Test 2: All WHITE pixels (all 0x00 bytes)")
        print("   Expected: Blank/white label\n")
        
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        # Send all white (0x00 = no bits set)
        for y in range(height):
            line_data = bytes([0x00] * 48)
            packet = NiimbotPacket(0x85, line_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Test 2 sent (all white)\n")
        await asyncio.sleep(2)
        
        print("🧪 Test 3: Alternating bytes (0xFF, 0x00, 0xFF, 0x00...)")
        print("   Expected: Vertical stripes (8 pixels black, 8 pixels white)\n")
        
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        # Alternating pattern
        for y in range(height):
            line_data = bytes([0xFF, 0x00] * 24)  # Repeat pattern
            packet = NiimbotPacket(0x85, line_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Test 3 sent (alternating)\n")
        await asyncio.sleep(2)
        
        print("🧪 Test 4: Single bit pattern (0x80 = 10000000)")
        print("   Expected: Thin vertical line on left edge\n")
        
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        # First bit set only
        for y in range(height):
            line_data = bytes([0x80] + [0x00] * 47)  # First bit set, rest clear
            packet = NiimbotPacket(0x85, line_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        
        print("✅ Test 4 sent (single bit)\n")
        
        print("\n" + "="*60)
        print("📋 ANALYSIS:")
        print("="*60)
        print("After printing, check the results:")
        print("  Test 1 (0xFF): If BLACK → bit 1 = black pixel ✓")
        print("                  If WHITE → bit 1 = white pixel (inverted!)")
        print("  Test 2 (0x00): Should be opposite of Test 1")
        print("  Test 3: Should show clear vertical stripe pattern")
        print("  Test 4: Should show where bit position 0 is located")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_raw_pixels())
