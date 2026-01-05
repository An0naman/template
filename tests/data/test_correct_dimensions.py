#!/usr/bin/env python3
"""
Test correct B1 dimensions - image should fill one label exactly
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

def create_full_width_test():
    """
    Create image that uses FULL width of B1 printhead
    
    B1 specs:
    - Printhead: 384 pixels wide (50mm @ 203 DPI)
    - For a 14mm tall label: 110 pixels
    
    When printing:
    - Paper feeds vertically
    - Printhead is horizontal (384px wide)
    - So image should be: 384 wide x however tall we want
    """
    
    # For a single 50x14mm label that prints correctly:
    # We want 110 pixels tall (14mm) in the feed direction
    # And 384 pixels wide (50mm) across the printhead
    
    width = 384   # Full printhead width
    height = 110  # 14mm label height
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Fill with test pattern
    # Border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
    
    # Stripes to show we're using full width
    for x in range(0, width, 40):
        draw.rectangle([x, 0, x+20, height], fill='lightgray')
    
    # Big text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = None
    
    draw.text((width//2, height//2), "FULL WIDTH TEST", 
              fill='black', font=font, anchor='mm')
    
    # Corner markers
    draw.text((10, 10), "TL", fill='black', anchor='lt')
    draw.text((width-10, 10), "TR", fill='black', anchor='rt')
    draw.text((10, height-10), "BL", fill='black', anchor='lb')
    draw.text((width-10, height-10), "BR", fill='black', anchor='rb')
    
    print(f"Created image: {width}x{height} pixels")
    print(f"  Width:  {width}px = {width * 25.4 / 203:.1f}mm (should be ~50mm)")
    print(f"  Height: {height}px = {height * 25.4 / 203:.1f}mm (should be ~14mm)")
    
    return img

async def main():
    """Test with no rotation first"""
    
    print("\n" + "="*60)
    print("B1 Full Width Test - NO ROTATION")
    print("="*60 + "\n")
    
    img = create_full_width_test()
    
    print("\nPrinting without rotation...")
    print("Expected result: ONE label, FULL WIDTH, text readable")
    print()
    
    async with NiimbotPrinterBLE("B1", model="b1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return
        
        print("✅ Connected, printing...")
        success = await printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("\n✅ Print complete!")
            print("\nCheck the result:")
            print("  • Does it fill ONE label completely?")
            print("  • Is text readable?")
            print("  • Can you see all corner markers (TL, TR, BL, BR)?")
        else:
            print("\n❌ Print failed")

if __name__ == "__main__":
    asyncio.run(main())
