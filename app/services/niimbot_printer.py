"""
Niimbot Printer Service
Handles Bluetooth connectivity and printing to Niimbot label printers (B1, D110)
Uses RFCOMM (Classic Bluetooth), not BLE
Based on the niimprint library protocol
"""

import asyncio
import logging
import struct
import math
import socket
from enum import IntEnum
from typing import Optional, List, Dict
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


class InfoEnum(IntEnum):
    """Printer information types"""
    DENSITY = 1
    PRINTSPEED = 2
    LABELTYPE = 3
    LANGUAGETYPE = 6
    AUTOSHUTDOWNTIME = 7
    DEVICETYPE = 8
    SOFTVERSION = 9
    BATTERY = 10
    DEVICESERIAL = 11
    HARDVERSION = 12


class RequestCodeEnum(IntEnum):
    """Printer request codes"""
    GET_INFO = 64  # 0x40
    GET_RFID = 26  # 0x1A
    HEARTBEAT = 220  # 0xDC
    SET_LABEL_TYPE = 35  # 0x23
    SET_LABEL_DENSITY = 33  # 0x21
    START_PRINT = 1  # 0x01
    END_PRINT = 243  # 0xF3
    START_PAGE_PRINT = 3  # 0x03
    END_PAGE_PRINT = 227  # 0xE3
    ALLOW_PRINT_CLEAR = 32  # 0x20
    SET_DIMENSION = 19  # 0x13
    SET_QUANTITY = 21  # 0x15
    GET_PRINT_STATUS = 163  # 0xA3


class NiimbotPacket:
    """Niimbot communication packet"""
    def __init__(self, type_: int, data: bytes = b""):
        self.type = type_
        self.data = data

    def to_bytes(self) -> bytes:
        """Convert packet to bytes for transmission"""
        checksum = self.type ^ len(self.data)
        for i in self.data:
            checksum ^= i
        return bytes([0x55, 0x55, self.type, len(self.data), *self.data, checksum, 0xAA, 0xAA])

    @staticmethod
    def from_bytes(data: bytes) -> Optional['NiimbotPacket']:
        """Parse packet from received bytes"""
        if len(data) < 7 or data[0:2] != b'\x55\x55' or data[-2:] != b'\xAA\xAA':
            return None
        type_ = data[2]
        len_ = data[3]
        packet_data = data[4:4+len_]
        
        # Verify checksum
        checksum = type_ ^ len_
        for i in packet_data:
            checksum ^= i
        if checksum != data[-3]:
            logger.warning(f"Checksum mismatch: expected {data[-3]}, got {checksum}")
            return None
            
        return NiimbotPacket(type_, packet_data)


def packet_to_int(packet: NiimbotPacket) -> int:
    """Convert packet data to integer"""
    if not packet.data:
        return 0
    return int.from_bytes(packet.data, byteorder='big')


class NiimbotPrinter:
    """Niimbot printer client for Bluetooth RFCOMM communication"""

    def __init__(self, address: str, model: str = "d110"):
        """
        Initialize Niimbot printer client
        
        Args:
            address: Bluetooth device address
            model: Printer model (b1, d110, etc.)
        """
        self.address = address
        self.model = model.lower()
        self.client: Optional[BleakClient] = None
        self.char_uuid: Optional[str] = None
        self.notify_char_uuid: Optional[str] = None
        self.notification_event = asyncio.Event()
        self.notification_data: Optional[bytes] = None

    async def connect(self, timeout: float = 30.0, retries: int = 3) -> bool:
        """
        Connect to the printer with retries
        
        Args:
            timeout: Connection timeout in seconds
            retries: Number of connection attempts
        """
        if not BLEAK_AVAILABLE:
            logger.error("Bleak library not available")
            return False
        
        for attempt in range(retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{retries} to {self.address}")
                
                self.client = BleakClient(
                    self.address,
                    timeout=timeout
                )
                
                await self.client.connect()
                
                if not self.client.is_connected:
                    logger.warning(f"Connection attempt {attempt + 1} failed")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
                        continue
                    logger.error("Failed to connect to printer after all retries")
                    return False
                    
                logger.info(f"Successfully connected to Niimbot printer at {self.address}")
                
                # Find the correct characteristic
                await self._find_characteristics()
                
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
                    continue
                logger.error(f"Failed to connect after {retries} attempts")
                return False
        
        return False

    async def disconnect(self):
        """Disconnect from the printer"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logger.info("Disconnected from printer")

    async def _find_characteristics(self):
        """Find the correct characteristic UUID for communication"""
        services = self.client.services
        
        logger.info("=== Bluetooth GATT Services and Characteristics ===")
        for service in services:
            logger.info(f"Service: {service.uuid}")
            for char in service.characteristics:
                logger.info(f"  Characteristic: {char.uuid}, Properties: {char.properties}")
        
        # Try known write characteristics
        for service in services:
            for char in service.characteristics:
                if char.uuid.lower() in [uuid.lower() for uuid in self.WRITE_CHAR_UUIDS]:
                    self.char_uuid = char.uuid
                    logger.info(f"✓ Found known write characteristic: {self.char_uuid}")
                    break
            if self.char_uuid:
                break
        
        # Try known notify characteristics
        for service in services:
            for char in service.characteristics:
                if char.uuid.lower() in [uuid.lower() for uuid in self.NOTIFY_CHAR_UUIDS]:
                    self.notify_char_uuid = char.uuid
                    logger.info(f"✓ Found known notify characteristic: {self.notify_char_uuid}")
                    if 'notify' in char.properties:
                        await self.client.start_notify(self.notify_char_uuid, self._notification_handler)
                        logger.info(f"✓ Started notifications on {self.notify_char_uuid}")
                    break
            if self.notify_char_uuid:
                break
        
        if self.char_uuid and self.notify_char_uuid:
            logger.info("✓ Communication characteristics configured successfully")
            return
        
        # Fallback: Search by service UUID
        logger.warning("Known characteristics not found, searching by service UUID...")
        for service_uuid in self.SERVICE_UUIDS:
            for service in services:
                if service.uuid.lower() == service_uuid.lower():
                    logger.info(f"Found known service: {service.uuid}")
                    
                    for char in service.characteristics:
                        if not self.char_uuid and 'write' in char.properties:
                            self.char_uuid = char.uuid
                            logger.info(f"  Using write characteristic: {char.uuid}")
                        if not self.notify_char_uuid and 'notify' in char.properties:
                            self.notify_char_uuid = char.uuid
                            logger.info(f"  Using notify characteristic: {char.uuid}")
                    
                    if self.char_uuid and self.notify_char_uuid:
                        await self.client.start_notify(self.notify_char_uuid, self._notification_handler)
                        logger.info(f"✓ Started notifications")
                        return
        
        logger.error("Could not find suitable characteristics!")
        raise Exception("No suitable GATT characteristics found for communication")

    def _notification_handler(self, sender, data: bytearray):
        """Handle notifications from printer"""
        self.notification_data = bytes(data)
        self.notification_event.set()

    async def _send_command(self, request_code: RequestCodeEnum, data: bytes = b"", timeout: float = 5.0) -> Optional[NiimbotPacket]:
        """Send command to printer and wait for response"""
        packet = NiimbotPacket(request_code, data)
        
        self.notification_event.clear()
        self.notification_data = None
        
        # Use the write characteristic
        await self.client.write_gatt_char(self.char_uuid, packet.to_bytes())
        logger.debug(f"Sent command {request_code} to {self.char_uuid}")
        
        try:
            await asyncio.wait_for(self.notification_event.wait(), timeout=timeout)
            if self.notification_data:
                response = NiimbotPacket.from_bytes(self.notification_data)
                logger.debug(f"Received response for command {request_code}")
                return response
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response to command {request_code}")
            return None

    async def _write_raw(self, packet: NiimbotPacket):
        """Write raw packet without waiting for response"""
        await self.client.write_gatt_char(self.char_uuid, packet.to_bytes())

    async def get_info(self, key: InfoEnum) -> Optional[any]:
        """Get printer information"""
        response = await self._send_command(RequestCodeEnum.GET_INFO, bytes((key,)))
        if not response:
            return None
            
        if key == InfoEnum.DEVICESERIAL:
            return response.data.hex()
        elif key in (InfoEnum.SOFTVERSION, InfoEnum.HARDVERSION):
            return packet_to_int(response) / 100
        else:
            return packet_to_int(response)

    async def heartbeat(self) -> Dict:
        """Send heartbeat to printer"""
        response = await self._send_command(RequestCodeEnum.HEARTBEAT, b"\x01")
        if not response or len(response.data) < 13:
            return {}
        
        try:
            return {
                'closingState': response.data[0],
                'powerLevel': response.data[1],
                'paperState': response.data[2],
                'rfidReadState': response.data[3],
                'printingCompleted': response.data[9] == 1,
            }
        except Exception as e:
            logger.error(f"Error parsing heartbeat: {e}")
            return {}

    async def set_label_type(self, n: int = 1) -> bool:
        """Set label type (1-3)"""
        assert 1 <= n <= 3
        response = await self._send_command(RequestCodeEnum.SET_LABEL_TYPE, bytes((n,)))
        return response and bool(response.data[0]) if response else False

    async def set_label_density(self, n: int = 3) -> bool:
        """Set print density (1-5)"""
        assert 1 <= n <= 5
        response = await self._send_command(RequestCodeEnum.SET_LABEL_DENSITY, bytes((n,)))
        return response and bool(response.data[0]) if response else False

    async def start_print(self) -> bool:
        """Start print job"""
        response = await self._send_command(RequestCodeEnum.START_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    async def end_print(self) -> bool:
        """End print job"""
        response = await self._send_command(RequestCodeEnum.END_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    async def start_page_print(self) -> bool:
        """Start page print"""
        response = await self._send_command(RequestCodeEnum.START_PAGE_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    async def end_page_print(self) -> bool:
        """End page print"""
        response = await self._send_command(RequestCodeEnum.END_PAGE_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    async def set_dimension(self, width: int, height: int) -> bool:
        """Set print dimensions"""
        response = await self._send_command(RequestCodeEnum.SET_DIMENSION, struct.pack(">HH", width, height))
        return response and bool(response.data[0]) if response else False

    async def set_quantity(self, n: int) -> bool:
        """Set print quantity"""
        response = await self._send_command(RequestCodeEnum.SET_QUANTITY, struct.pack(">H", n))
        return response and bool(response.data[0]) if response else False

    async def get_print_status(self) -> Dict:
        """Get current print status"""
        response = await self._send_command(RequestCodeEnum.GET_PRINT_STATUS, b"\x01")
        if not response or len(response.data) < 4:
            return {}
        
        try:
            page, progress1, progress2 = struct.unpack(">HBB", response.data)
            return {"page": page, "progress1": progress1, "progress2": progress2}
        except Exception as e:
            logger.error(f"Error parsing print status: {e}")
            return {}

    def _encode_image(self, image: Image, vertical_offset: int = 0, horizontal_offset: int = 0):
        """Encode image for printing"""
        # Convert to monochrome
        img = ImageOps.invert(image.convert("L")).convert("1")

        # Apply horizontal offset
        if horizontal_offset > 0:
            img = ImageOps.expand(img, border=(horizontal_offset, 0, 0, 0), fill=1)
        elif horizontal_offset < 0:
            img = img.crop((-horizontal_offset, 0, img.width, img.height))

        # Add vertical padding
        if vertical_offset > 0:
            img = ImageOps.expand(img, border=(0, vertical_offset, 0, 0), fill=1)

        # Yield packets for each line
        for y in range(img.height):
            line_data = [img.getpixel((x, y)) for x in range(img.width)]
            line_data = "".join("0" if pix == 0 else "1" for pix in line_data)
            line_data = int(line_data, 2).to_bytes(math.ceil(img.width / 8), "big")
            
            counts = (0, 0, 0)
            header = struct.pack(">H3BB", y, *counts, 1)
            yield NiimbotPacket(0x85, header + line_data)

    async def print_image(self, image: Image, density: int = 3, quantity: int = 1, 
                         vertical_offset: int = 0, horizontal_offset: int = 0) -> bool:
        """
        Print an image to the label printer
        
        Args:
            image: PIL Image to print
            density: Print density (1-5)
            quantity: Number of copies to print
            vertical_offset: Vertical offset in pixels
            horizontal_offset: Horizontal offset in pixels
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting print job: density={density}, quantity={quantity}")
            
            await self.set_label_density(density)
            await self.set_label_type(1)
            await self.start_print()
            await self.start_page_print()
            await self.set_dimension(image.height, image.width)
            await self.set_quantity(quantity)

            # Send image data
            for packet in self._encode_image(image, vertical_offset, horizontal_offset):
                await self._write_raw(packet)
                await asyncio.sleep(0.01)  # Small delay to prevent buffer overflow

            # Wait for page print to complete
            while not await self.end_page_print():
                await asyncio.sleep(0.05)

            # Wait for all copies to print
            while True:
                status = await self.get_print_status()
                if status.get('page', 0) >= quantity:
                    break
                await asyncio.sleep(0.1)

            await self.end_print()
            logger.info("Print job completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during print: {e}")
            try:
                await self.end_print()
            except:
                pass
            return False


async def discover_niimbot_printers(timeout: float = 10.0) -> List[Dict]:
    """
    Discover Niimbot printers via Bluetooth
    
    Args:
        timeout: Scan timeout in seconds
        
    Returns:
        List of discovered printers with name and address
    """
    if not BLEAK_AVAILABLE:
        logger.error("Bleak library not available")
        return []
    
    try:
        logger.info(f"Scanning for Niimbot printers (timeout: {timeout}s)...")
        devices = await BleakScanner.discover(timeout=timeout)
        
        niimbot_devices = []
        for device in devices:
            if device.name and ('niimbot' in device.name.lower() or 
                               'b1' in device.name.lower() or 
                               'd110' in device.name.lower() or
                               'd11' in device.name.lower() or
                               'b21' in device.name.lower()):
                niimbot_devices.append({
                    'name': device.name,
                    'address': device.address,
                    'rssi': device.rssi if hasattr(device, 'rssi') else None
                })
                logger.info(f"Found Niimbot printer: {device.name} ({device.address})")
        
        return niimbot_devices
        
    except Exception as e:
        logger.error(f"Error discovering printers: {e}")
        return []


async def find_printer_by_model(model: str, timeout: float = 10.0) -> Optional[Dict]:
    """
    Find a specific Niimbot printer by model
    
    Args:
        model: Printer model (b1, d110, etc.)
        timeout: Scan timeout in seconds
        
    Returns:
        Printer info dict or None if not found
    """
    devices = await discover_niimbot_printers(timeout)
    model_lower = model.lower()
    
    for device in devices:
        if model_lower in device['name'].lower():
            return device
    
    return None
