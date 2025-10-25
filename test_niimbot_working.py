#!/usr/bin/env python3
"""Test Niimbot printer with working configuration"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient

PRINTERS = {
    "B1": "13:07:12:A6:40:07",
    "D110": "C3:33:D5:02:36:62"
}

# Working characteristic UUID
CHAR_UUID = "bef8d6c9-9c21-4c9e-b632-bd58c1009f9f"

def calculate_checksum(cmd, data):
    """Calculate XOR checksum for packet"""
    checksum = cmd ^ len(data)
    for byte in data:
        checksum ^= byte
    return checksum

def make_packet(cmd, data=b''):
    """Create NiimPrintX packet with correct checksum"""
    checksum = calculate_checksum(cmd, data)
    return bytes([0x55, 0x55, cmd, len(data), *data, checksum, 0xAA, 0xAA])

def decode_response(data):
    """Decode printer response"""
    if len(data) < 8:
        return f"Too short: {data.hex()}"
    
    if data[0] != 0x55 or data[1] != 0x55:
        return f"Invalid header: {data.hex()}"
    
    cmd = data[2]
    length = data[3]
    payload = data[4:4+length]
    checksum = data[4+length]
    
    cmd_names = {
        0xDD: "HEARTBEAT_RESP",
        0xDC: "HEARTBEAT",
        0xBF: "GET_INFO",
        0xC0: "INFO_RESP",
        0x85: "PRINT",
    }
    
    result = f"Cmd: {cmd_names.get(cmd, f'0x{cmd:02x}')} | Len: {length} | Data: {payload.hex()}"
    
    # Decode heartbeat response
    if cmd == 0xDD and length == 13:
        # Bytes breakdown based on official protocol
        status = payload[0]  # 0x1e
        paper_type = payload[1]  # 0x89
        unknown = payload[2:6].hex()  # 005d005d
        label_width = int.from_bytes(payload[6:8], 'big')  # 0x004b = 75mm
        label_height = int.from_bytes(payload[8:10], 'big')  # 0x0002 
        unknown2 = payload[10:13].hex()
        
        result += f"\n  Status: 0x{status:02x}, Paper: 0x{paper_type:02x}, Width: {label_width}mm"
    
    return result

async def test_printer(address):
    """Test printer commands"""
    print(f"\n{'='*60}")
    print(f"Testing printer: {address}")
    print('='*60)
    
    response_data = []
    
    def notification_handler(sender, data):
        print(f"📨 Response: {data.hex()}")
        print(f"   {decode_response(data)}")
        response_data.append(data)
    
    async with BleakClient(address) as client:
        print(f"✅ Connected to {address}")
        
        # Start notifications
        await client.start_notify(CHAR_UUID, notification_handler)
        print(f"✓ Notifications started on {CHAR_UUID}")
        
        # Test 1: Heartbeat
        print("\n🧪 Test 1: Heartbeat (0xDC)")
        packet = make_packet(0xDC, b'\x01')
        print(f"   Sending: {packet.hex()}")
        await client.write_gatt_char(CHAR_UUID, packet)
        await asyncio.sleep(1)
        
        # Test 2: Get printer info
        print("\n🧪 Test 2: Get Info (0xBF)")
        response_data.clear()
        packet = make_packet(0xBF, b'\x01')
        print(f"   Sending: {packet.hex()}")
        await client.write_gatt_char(CHAR_UUID, packet)
        await asyncio.sleep(1)
        
        # Test 3: Get RFID info
        print("\n🧪 Test 3: Get RFID (0x1A)")
        response_data.clear()
        packet = make_packet(0x1A, b'\x01')
        print(f"   Sending: {packet.hex()}")
        await client.write_gatt_char(CHAR_UUID, packet)
        await asyncio.sleep(1)
        
        await client.stop_notify(CHAR_UUID)
        print("\n✅ Tests complete!")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_niimbot_working.py <B1|D110|ADDRESS>")
        sys.exit(1)
    
    target = sys.argv[1].upper()
    address = PRINTERS.get(target, target)
    
    await test_printer(address)

if __name__ == "__main__":
    asyncio.run(main())
