#!/usr/bin/env python3
"""
Test Niimbot printer with RFCOMM (Classic Bluetooth)
"""

import sys
sys.path.insert(0, '/home/an0naman/Documents/GitHub/template')

from app.services.niimbot_printer_rfcomm import NiimbotPrinter, InfoEnum
from PIL import Image, ImageDraw, ImageFont

# Your printer addresses
B1_ADDRESS = "13:07:12:A6:40:07"
D110_ADDRESS = "C3:33:D5:02:36:62"

def test_connection(address, model):
    """Test basic connection and info retrieval"""
    print(f"\n{'='*70}")
    print(f"Testing {model.upper()} at {address}")
    print('='*70)
    
    printer = NiimbotPrinter(address, model)
    
    if not printer.connect():
        print("❌ Failed to connect!")
        return False
    
    print("✅ Connected successfully!\n")
    
    try:
        # Get printer info
        print("Getting printer information...")
        device_type = printer.get_info(InfoEnum.DEVICETYPE)
        print(f"  Device Type: {device_type}")
        
        battery = printer.get_info(InfoEnum.BATTERY)
        print(f"  Battery: {battery}%")
        
        serial = printer.get_info(InfoEnum.DEVICESERIAL)
        print(f"  Serial: {serial}")
        
        # Heartbeat
        print("\nSending heartbeat...")
        status = printer.heartbeat()
        print(f"  Status: {status}")
        
        print("\n✅ Communication successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        printer.disconnect()


def test_print(address, model):
    """Test printing a simple label"""
    print(f"\n{'='*70}")
    print(f"Test Print - {model.upper()}")
    print('='*70)
    
    printer = NiimbotPrinter(address, model)
    
    if not printer.connect():
        print("❌ Failed to connect!")
        return False
    
    try:
        # Create a simple test image
        # D110 max width: 96 pixels, B1 max width: 384 pixels
        width = 96 if model == 'd110' else 384
        height = 120
        
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw some text
        text = f"Test {model.upper()}"
        draw.text((10, 40), text, fill='black')
        draw.rectangle([10, 10, width-10, height-10], outline='black', width=2)
        
        print(f"Printing {width}x{height}px test label...")
        
        success = printer.print_image(img, density=3, quantity=1)
        
        if success:
            print("✅ Print successful!")
        else:
            print("❌ Print failed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        printer.disconnect()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("NIIMBOT RFCOMM CONNECTION TEST")
    print("="*70)
    
    # Test D110
    print("\n🔧 Testing D110...")
    if test_connection(D110_ADDRESS, 'd110'):
        print("\nDo you want to test printing? (y/n): ", end='')
        if input().lower() == 'y':
            test_print(D110_ADDRESS, 'd110')
    
    # Test B1
    print("\n🔧 Testing B1...")
    if test_connection(B1_ADDRESS, 'b1'):
        print("\nDo you want to test printing? (y/n): ", end='')
        if input().lower() == 'y':
            test_print(B1_ADDRESS, 'b1')
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
