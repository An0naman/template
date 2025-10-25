#!/usr/bin/env python3
"""Test Niimbot B1 with RFCOMM (Classic Bluetooth)"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw
from app.services.niimbot_printer_rfcomm import NiimbotPrinter

def test_rfcomm_print():
    """Test print with RFCOMM"""
    
    # B1 address
    address = "13:07:12:A6:40:07"
    
    print(f"Connecting to B1 via RFCOMM at {address}...")
    printer = NiimbotPrinter(address, model="b1")
    
    if not printer.connect():
        print("❌ Connection failed")
        print("\n💡 Make sure:")
        print("   1. Printer is paired via bluetoothctl")
        print("   2. Using RFCOMM address (check with 'bluetoothctl info')")
        return
    
    print("✅ Connected!")
    
    # Create simple test image
    width = 384
    height = 50
    
    print(f"\n🖼️  Creating test image ({width}x{height}px)...")
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw test pattern
    draw.rectangle([10, 10, width-10, height-10], outline='black', width=3)
    draw.text((width//2, height//2), "NIIMBOT B1 TEST", fill='black', anchor='mm')
    
    print("📤 Printing...")
    success = printer.print_image(img, density=3, quantity=1)
    
    if success:
        print("✅ Print completed!")
    else:
        print("❌ Print failed")
    
    printer.disconnect()

if __name__ == "__main__":
    test_rfcomm_print()
