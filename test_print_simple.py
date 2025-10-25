#!/usr/bin/env python3
"""Simple print test - prints a small test label"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

async def print_test_label(printer_model: str):
    """Print a simple test label"""
    
    print(f"\n{'='*60}")
    print(f"Printing Test Label to {printer_model}")
    print('='*60)
    
    # Determine printer dimensions
    if printer_model.upper() == "B1":
        # B1: 32mm width (384 pixels at 12 pixels/mm)
        # For a small test, use 384px width x 200px height
        width = 384
        height = 200
    else:
        # D110: 15mm width (180 pixels at 12 pixels/mm)
        # For a small test, use 180px width x 150px height
        width = 180
        height = 150
    
    print(f"Creating label: {width}x{height}px")
    
    # Create white background image
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw a thick border
    draw.rectangle([5, 5, width-6, height-6], outline='black', width=3)
    
    # Draw text in the center
    center_x = width // 2
    
    # Try to use a built-in font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    # Draw text
    draw.text((center_x, 40), "NIIMBOT", fill='black', anchor='mm', font=font)
    draw.text((center_x, 80), printer_model.upper(), fill='black', anchor='mm', font=font)
    draw.text((center_x, 120), "TEST LABEL", fill='black', anchor='mm', font=font_small)
    draw.text((center_x, height-30), "✓ SUCCESS", fill='black', anchor='mm', font=font_small)
    
    # Draw some decorative elements
    draw.ellipse([center_x-10, 10, center_x+10, 30], outline='black', width=2)
    draw.ellipse([center_x-10, height-30, center_x+10, height-10], outline='black', width=2)
    
    # Save preview
    preview_path = f"test_label_{printer_model.lower()}_preview.png"
    img.save(preview_path)
    print(f"✓ Preview saved: {preview_path}")
    
    # Connect and print
    print(f"\nConnecting to {printer_model}...")
    async with NiimbotPrinterBLE(printer_model) as printer:
        if not printer.connected:
            print("❌ Connection failed")
            return False
        
        print("✅ Connected!")
        
        # Get RFID to check if label is loaded
        print("\nChecking for loaded label...")
        rfid = await printer.get_rfid()
        if rfid:
            print(f"✅ Label detected: {rfid.get('barcode', 'Unknown')}")
        else:
            print("⚠️  No RFID detected - printing may not work without label")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        # Print with density 3 (medium), 1 copy
        print(f"\n📤 Sending {width}x{height}px image to printer...")
        print("⏳ This may take 30-60 seconds...")
        
        success = await printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("\n✅ Print completed successfully!")
            print("🎉 Check your printer for the label!")
            return True
        else:
            print("\n❌ Print failed")
            return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_print_simple.py <B1|D110>")
        print("\nExamples:")
        print("  python test_print_simple.py B1")
        print("  python test_print_simple.py D110")
        sys.exit(1)
    
    printer_model = sys.argv[1].upper()
    if printer_model not in ["B1", "D110"]:
        print(f"❌ Unknown printer: {printer_model}")
        print("Valid options: B1, D110")
        sys.exit(1)
    
    success = await print_test_label(printer_model)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
