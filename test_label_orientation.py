#!/usr/bin/env python3
"""
Test different label orientations for B1 printer
Helps you find the correct rotation for your label loading direction
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from app.services.niimbot_printer_ble import NiimbotPrinterBLE

def create_test_label(rotation_text):
    """Create a test label with orientation indicator"""
    # Standard B1 label size: 384x110 pixels (50x14mm @ 203 DPI)
    width = 384
    height = 110
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    
    # Draw arrow pointing up
    arrow_x = width // 4
    arrow_y = height // 2
    draw.polygon([
        (arrow_x, arrow_y - 20),      # Top point
        (arrow_x - 15, arrow_y + 10),  # Bottom left
        (arrow_x + 15, arrow_y + 10)   # Bottom right
    ], fill='black')
    draw.text((arrow_x - 15, arrow_y + 15), "TOP", fill='black')
    
    # Draw text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = None
    
    draw.text((width // 2, height // 2), rotation_text, fill='black', 
              font=font, anchor='mm')
    
    return img

async def test_rotation(rotation_degrees):
    """Test a specific rotation"""
    print(f"\n{'='*60}")
    print(f"Testing rotation: {rotation_degrees}°")
    print(f"{'='*60}")
    
    # Create label
    label_img = create_test_label(f"Rotation: {rotation_degrees}°")
    
    # Apply rotation
    if rotation_degrees != 0:
        rotated = label_img.rotate(rotation_degrees, Image.Resampling.NEAREST, expand=True)
        print(f"Original size: {label_img.size}")
        print(f"Rotated size:  {rotated.size}")
    else:
        rotated = label_img
        print(f"Size: {label_img.size} (no rotation)")
    
    # Print
    async with NiimbotPrinterBLE("B1", model="b1") as printer:
        if not printer.connected:
            print("❌ Failed to connect")
            return False
        
        print("✅ Connected, printing...")
        success = await printer.print_image(rotated, density=3, quantity=1)
        
        if success:
            print("✅ Print complete!")
            return True
        else:
            print("❌ Print failed")
            return False

async def main():
    """Test different rotations"""
    print("=" * 60)
    print("B1 Label Orientation Test")
    print("=" * 60)
    print()
    print("This will print 4 test labels with different rotations.")
    print("Look at which one prints correctly oriented.")
    print()
    print("The arrow should point to the TOP of the label.")
    print()
    
    rotations = [
        ("0°   (no rotation)", 0),
        ("90°  (clockwise)", 90),
        ("-90° (counter-clockwise)", -90),
        ("180° (upside down)", 180)
    ]
    
    print("Available rotations to test:")
    for i, (desc, deg) in enumerate(rotations, 1):
        print(f"  {i}. {desc}")
    print()
    
    choice = input("Test all (a) or choose one (1-4)? [a]: ").strip().lower()
    
    if choice in ['1', '2', '3', '4']:
        idx = int(choice) - 1
        desc, deg = rotations[idx]
        await test_rotation(deg)
    else:
        # Test all
        for desc, deg in rotations:
            await test_rotation(deg)
            if deg != 180:  # Don't wait after last one
                print("\nWaiting 3 seconds before next test...")
                await asyncio.sleep(3)
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nWhich rotation looked correct?")
    print("Update your API call to use:")
    print('  {"rotation": <degrees>}')
    print("\nExamples:")
    print('  curl -X POST .../niimbot/print -d \'{"rotation": 90, ...}\'')

if __name__ == "__main__":
    asyncio.run(main())
