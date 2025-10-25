#!/usr/bin/env python3
"""Test print sequence with explicit feed command"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.niimbot_printer_ble import NiimbotPrinterBLE, NiimbotPacket

async def test_with_feed():
    """Complete print sequence with feed command"""
    
    async with NiimbotPrinterBLE("B1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected\n")
        
        width = 384
        height = 20
        
        # Create solid black pattern
        print("🖼️  Creating test pattern: solid black")
        test_data = bytes([0xFF] * 48)  # All bits set = should be black
        
        print("📋 Print sequence:")
        print("   1. Start print...")
        await printer.start_print()
        
        print("   2. Set density...")
        await printer.set_label_density(5)  # Max density for visibility
        
        print("   3. Set dimension...")
        await printer.set_dimension(width, height)
        
        print("   4. Set quantity...")
        await printer.set_quantity(1)
        
        print("   5. Start page...")
        await printer.start_page_print()
        
        print(f"   6. Send {height} lines of data...")
        for y in range(height):
            packet = NiimbotPacket(0x85, test_data)
            await printer._send_packet(packet, wait_response=False)
        
        print("   7. End page...")
        await printer.end_page_print()
        
        print("   8. Allow print clear (0x20)...")
        packet = NiimbotPacket(0x20, b'')
        result = await printer._send_packet(packet)
        print(f"      Response: {result.data.hex() if result else 'None'}")
        
        print("   9. End print...")
        await printer.end_print()
        
        # NOW send feed command
        print("   10. 🚀 FEED COMMAND (0xF1)...")
        packet = NiimbotPacket(0xF1, b'')
        result = await printer._send_packet(packet)
        print(f"       Response: {result.data.hex() if result else 'None'}")
        
        await asyncio.sleep(3)
        
        print("\n✅ Complete!")
        print("   Check if label printed automatically (should be solid black)")
        print("   If blank, the data encoding is wrong")
        print("   If nothing printed, 0xF1 isn't the right trigger")

if __name__ == "__main__":
    asyncio.run(test_with_feed())
