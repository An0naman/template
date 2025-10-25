#!/usr/bin/env python3
"""
Test different label heights to find your actual label size
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

def create_test_label(width, height, label_info):
    """Create test label with specified dimensions"""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
    
    # Diagonal lines to see if it's cut off
    draw.line([(0, 0), (width, height)], fill='black', width=2)
    draw.line([(0, height), (width, 0)], fill='black', width=2)
    
    # Text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = font_small = None
    
    draw.text((width//2, height//2 - 15), label_info, 
              fill='black', font=font, anchor='mm')
    draw.text((width//2, height//2 + 10), f"{width}x{height}px", 
              fill='black', font=font_small, anchor='mm')
    
    # Corner markers
    marker_size = 10
    draw.ellipse([5, 5, 5+marker_size, 5+marker_size], fill='black')  # Top-left
    draw.ellipse([width-15, 5, width-5, 5+marker_size], fill='black')  # Top-right
    draw.ellipse([5, height-15, 5+marker_size, height-5], fill='black')  # Bottom-left
    draw.ellipse([width-15, height-15, width-5, height-5], fill='black')  # Bottom-right
    
    return img

async def test_size(width, height, label_info):
    """Test printing with specific dimensions"""
    print(f"\n{'='*60}")
    print(f"Testing: {label_info}")
    print(f"Size: {width}x{height} pixels = {width*25.4/203:.1f}x{height*25.4/203:.1f}mm")
    print(f"{'='*60}")
    
    img = create_test_label(width, height, label_info)
    
    async with NiimbotPrinterBLE("B1", model="b1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return False
        
        print("✅ Connected, printing...")
        success = await printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("✅ Print complete!")
            print("\nCheck the label:")
            print("  • Can you see all 4 corner circles?")
            print("  • Can you see both diagonal lines fully?")
            print("  • Is the text centered?")
            return True
        else:
            print("❌ Print failed")
            return False

async def main():
    """Test common B1 label sizes"""
    
    print("\n" + "="*60)
    print("B1 Label Size Detection")
    print("="*60)
    print("\nWe'll test different heights to find your actual label size.")
    print("Look for the one where you can see ALL 4 corner circles.\n")
    
    # Common B1 label sizes (width is always 384 for 50mm)
    test_sizes = [
        (384, 95,  "30x12mm"),   # 30mm wide x 12mm tall
        (384, 119, "30x15mm"),   # 30mm wide x 15mm tall
        (384, 158, "40x20mm"),   # 40mm wide x 20mm tall  
        (384, 189, "40x24mm"),   # 40mm wide x 24mm tall
        (384, 237, "60x30mm"),   # 60mm wide x 30mm tall
    ]
    
    choice = input("Test all sizes (a) or choose size (1-5)? [a]: ").strip().lower()
    
    if choice in ['1', '2', '3', '4', '5']:
        idx = int(choice) - 1
        width, height, label = test_sizes[idx]
        await test_size(width, height, label)
    else:
        # Test all
        for i, (width, height, label) in enumerate(test_sizes, 1):
            print(f"\n\n>>> Test {i}/{len(test_sizes)}")
            await test_size(width, height, label)
            if i < len(test_sizes):
                input("\nPress Enter for next test...")
    
    print("\n" + "="*60)
    print("Which label showed all 4 corner circles correctly?")
    print("Update your label configuration with that size!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
