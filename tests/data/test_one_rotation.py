#!/usr/bin/env python3
"""
Quick orientation test - Print one label with a specific rotation
Usage: python test_one_rotation.py [0|90|-90|180]
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

def create_orientation_test_label(rotation_degrees):
    """Create a clear test label showing orientation"""
    # B1 label: 384x110 pixels (50x14mm)
    width = 384
    height = 110
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Border
    draw.rectangle([2, 2, width-3, height-3], outline='black', width=3)
    
    # Big arrow pointing RIGHT (this is the TOP when label is horizontal)
    arrow_center_x = width // 2
    arrow_center_y = height // 2
    arrow_size = 30
    
    # Draw arrow: ►
    draw.polygon([
        (arrow_center_x + arrow_size, arrow_center_y),         # Point (right)
        (arrow_center_x - arrow_size//2, arrow_center_y - arrow_size//2),  # Top left
        (arrow_center_x - arrow_size//2, arrow_center_y + arrow_size//2),  # Bottom left
    ], fill='black')
    
    # Text above arrow
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = font_small = None
    
    draw.text((arrow_center_x, 15), "→ THIS SIDE UP →", 
              fill='black', font=font_small, anchor='mt')
    draw.text((arrow_center_x, height - 15), f"Rotation: {rotation_degrees}°", 
              fill='black', font=font_small, anchor='mb')
    
    return img

async def main():
    """Test a specific rotation"""
    if len(sys.argv) > 1:
        try:
            rotation = int(sys.argv[1])
        except ValueError:
            print("Usage: python test_one_rotation.py [0|90|-90|180]")
            print("Example: python test_one_rotation.py 90")
            sys.exit(1)
    else:
        print("Enter rotation degrees (0, 90, -90, or 180): ", end='')
        rotation = int(input().strip())
    
    print(f"\n{'='*60}")
    print(f"Testing Rotation: {rotation}°")
    print(f"{'='*60}\n")
    
    # Create label
    label = create_orientation_test_label(rotation)
    print(f"Generated label: {label.size[0]}x{label.size[1]} pixels")
    
    # Apply rotation
    if rotation != 0:
        rotated = label.rotate(rotation, Image.Resampling.NEAREST, expand=True)
        print(f"After rotation:  {rotated.size[0]}x{rotated.size[1]} pixels")
    else:
        rotated = label
        print("No rotation applied")
    
    print(f"\nLook for:")
    print("  - Arrow pointing UP")
    print("  - Text '→ THIS SIDE UP →' at the top")
    print("  - Border around the label")
    print()
    
    # Print
    async with NiimbotPrinterBLE("B1", model="b1") as printer:
        if not printer.connected:
            print("❌ Failed to connect to B1")
            return
        
        print("✅ Connected, printing...")
        success = await printer.print_image(rotated, density=3, quantity=1)
        
        if success:
            print("\n✅ Print complete!")
            print(f"\n{'='*60}")
            print("Check the label:")
            print(f"  • Is the arrow pointing UP? ✓ Correct!")
            print(f"  • Arrow pointing another direction? Try different rotation.")
            print(f"{'='*60}\n")
            print("If this rotation is correct, update your API calls:")
            print(f'  {{"rotation": {rotation}}}')
        else:
            print("\n❌ Print failed")

if __name__ == "__main__":
    asyncio.run(main())
