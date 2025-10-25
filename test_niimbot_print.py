#!/usr/bin/env python3
"""Test Niimbot printer full workflow including image printing"""

import asyncio
import sys
from PIL import Image, ImageDraw, ImageFont
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.niimbot_printer_ble import NiimbotPrinterBLE, scan_printers

async def test_print(printer_address: str):
    """Test complete print workflow"""
    
    print(f"\n{'='*60}")
    print(f"Testing Niimbot Printer: {printer_address}")
    print('='*60)
    
    async with NiimbotPrinterBLE(printer_address) as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("\n✅ Connected!")
        
        # Test 1: Get printer info
        print("\n🧪 Test 1: Get Printer Info")
        battery = await printer.get_info(10)  # Battery level
        if battery:
            print(f"   Battery: {battery}%")
        
        serial = await printer.get_info(11)  # Serial number
        if serial:
            print(f"   Serial: {serial}")
        
        # Test 2: Get RFID info
        print("\n🧪 Test 2: Get RFID Info")
        rfid = await printer.get_rfid()
        if rfid:
            print(f"   Barcode: {rfid.get('barcode', 'N/A')}")
            print(f"   Serial: {rfid.get('serial', 'N/A')}")
            if rfid.get('total_len'):
                print(f"   Label: {rfid.get('used_len', 0)}mm / {rfid.get('total_len', 0)}mm used")
        else:
            print("   No RFID tag detected (no label loaded?)")
        
        # Test 3: Create and print test label
        print("\n🧪 Test 3: Print Test Label")
        
        # Determine printer dimensions
        if "B1" in printer_address or "13:07:12:A6:40:07" in printer_address:
            # B1: 32mm width (384 pixels at 8 pixels/mm)
            label_width = 384
            label_height = 150
            model = "B1"
        else:
            # D110: 15mm width (120 pixels)
            label_width = 120
            label_height = 150
            model = "D110"
        
        print(f"   Creating test label for {model}: {label_width}x{label_height}px")
        
        # Create test image
        img = Image.new('RGB', (label_width, label_height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw border
        draw.rectangle([5, 5, label_width-6, label_height-6], outline='black', width=2)
        
        # Draw text
        draw.text((label_width//2, 30), "NIIMBOT", fill='black', anchor='mm')
        draw.text((label_width//2, 60), model, fill='black', anchor='mm')
        draw.text((label_width//2, 90), "TEST", fill='black', anchor='mm')
        draw.text((label_width//2, 120), "LABEL", fill='black', anchor='mm')
        
        # Print with density 3 (medium), 1 copy
        print("   📤 Sending to printer...")
        success = await printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("   ✅ Print completed successfully!")
        else:
            print("   ❌ Print failed")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_niimbot_print.py <B1|D110|ADDRESS|scan>")
        print("\nExamples:")
        print("  python test_niimbot_print.py scan          # Scan for printers")
        print("  python test_niimbot_print.py B1            # Print to B1")
        print("  python test_niimbot_print.py D110          # Print to D110")
        print("  python test_niimbot_print.py 13:07:12:A6:40:07  # Print to specific address")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if target.lower() == "scan":
        printers = await scan_printers()
        if not printers:
            print("No Niimbot printers found")
        sys.exit(0)
    
    await test_print(target)

if __name__ == "__main__":
    asyncio.run(main())
