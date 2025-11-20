#!/usr/bin/env python3
"""Test different print data commands"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_data_commands():
    """Try different commands for sending image data"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        width = 384
        height = 10
        
        # Create test pattern: all 0xFF (should be solid black)
        test_data = bytes([0xFF] * 48)  # 384 pixels / 8 = 48 bytes
        
        # Test 1: Try command 0x84 instead of 0x85
        print("🧪 Test 1: Using command 0x84 for image data")
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        for y in range(height):
            packet = NiimbotPacket(0x84, test_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        print("   ✅ Sent with 0x84\n")
        await asyncio.sleep(1)
        
        # Test 2: Try command 0x86
        print("🧪 Test 2: Using command 0x86 for image data")
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        for y in range(height):
            packet = NiimbotPacket(0x86, test_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        print("   ✅ Sent with 0x86\n")
        await asyncio.sleep(1)
        
        # Test 3: Try 0x85 with line number prefix
        print("🧪 Test 3: Using 0x85 with line number prefix")
        await printer.start_print()
        await printer.set_label_density(3)
        await printer.set_dimension(width, height)
        await printer.set_quantity(1)
        await printer.start_page_print()
        
        for y in range(height):
            # Add line number as first byte
            line_data = bytes([y]) + test_data
            packet = NiimbotPacket(0x85, line_data)
            await printer._send_packet(packet, wait_response=False)
        
        await printer.end_page_print()
        await printer.end_print()
        print("   ✅ Sent with 0x85 + line number\n")
        
        print("\n" + "="*60)
        print("📋 Now press the print button on your B1")
        print("   It should feed 3 labels")
        print("   Tell me if any show black patterns!")
        print("="*60)
        print("\nWaiting 60 seconds for you to press button...")
        
        for i in range(12):
            await asyncio.sleep(5)
            await printer.send_heartbeat()
            print(f"   {60 - (i+1)*5}s remaining...")

if __name__ == "__main__":
    asyncio.run(test_data_commands())
