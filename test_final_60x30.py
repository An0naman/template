#!/usr/bin/env python3
"""
Final test - Print a complete label with correct 60x30mm dimensions
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

def create_realistic_label():
    """Create a realistic label like your app would generate"""
    # 60x30mm at 203 DPI = 480x237 pixels
    # But B1 max width is 384px, so we use 384x237
    width = 384   # Max printhead width (48mm)
    height = 237  # 30mm height
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Border
    draw.rectangle([2, 2, width-3, height-3], outline='black', width=2)
    
    # Try to load fonts
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_title = font_normal = font_small = None
    
    # Title
    y_pos = 20
    draw.text((width//2, y_pos), "Wine Batch #42", 
              fill='black', font=font_title, anchor='mt')
    
    # Details
    y_pos += 45
    draw.text((10, y_pos), "Type: Blackberry Wine", 
              fill='black', font=font_normal, anchor='lt')
    
    y_pos += 30
    draw.text((10, y_pos), "Started: 2024-10-01", 
              fill='black', font=font_small, anchor='lt')
    
    y_pos += 25
    draw.text((10, y_pos), "Status: Fermenting", 
              fill='black', font=font_small, anchor='lt')
    
    # QR code placeholder (small box in bottom right)
    qr_size = 60
    draw.rectangle([width-qr_size-10, height-qr_size-10, width-10, height-10], 
                   outline='black', width=1)
    draw.text((width-qr_size//2-10, height-qr_size//2-10), "QR", 
              fill='black', font=font_small, anchor='mm')
    
    return img

async def main():
    """Test printing with correct 60x30mm dimensions"""
    
    print("\n" + "="*60)
    print("Final Test - Realistic 60x30mm Label")
    print("="*60)
    print("\nDimensions: 384x237 pixels (48x30mm)")
    print("Rotation: 0° (no rotation)")
    print("\nThis should print one complete label with:")
    print("  • Title at top")
    print("  • Details in middle")
    print("  • QR code placeholder in bottom right")
    print()
    
    img = create_realistic_label()
    
    async with NiimbotPrinterBLE("B1", model="b1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected, printing...")
        success = await printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("\n✅ Print complete!")
            print("\n" + "="*60)
            print("CHECK THE LABEL:")
            print("="*60)
            print("✓ Does it fill ONE 60x30mm label completely?")
            print("✓ Is all text readable?")
            print("✓ Is orientation correct (text readable without rotating)?")
            print("✓ No overflow to next label?")
            print("\nIf YES to all: Your B1 is configured correctly! 🎉")
            print("\nYou can now print from your app:")
            print('  POST /api/entries/<id>/niimbot/print')
            print('  {"printer_address": "B1", "printer_model": "b1"}')
        else:
            print("\n❌ Print failed")

if __name__ == "__main__":
    asyncio.run(main())
