"""
Niimbot Printer Service - BLE Version
Handles Bluetooth Low Energy connectivity and printing to Niimbot label printers (B1, D110)
Uses the correct BLE GATT characteristic UUID discovered through testing
"""

import asyncio
import logging
import struct
import math
from enum import IntEnum
from typing import Optional, List, Dict, Callable
from PIL import Image, ImageOps
from bleak import BleakScanner, BleakClient

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
    GET_INFO = 0xBF  # 191
    GET_RFID = 0x1A  # 26
    HEARTBEAT = 0xDC  # 220
    SET_LABEL_TYPE = 0x23  # 35
    SET_LABEL_DENSITY = 0x21  # 33
    START_PRINT = 0x01  # 1
    END_PRINT = 0xF3  # 243
    START_PAGE_PRINT = 0x03  # 3
    END_PAGE_PRINT = 0xE3  # 227
    ALLOW_PRINT_CLEAR = 0x20  # 32
    SET_DIMENSION = 0x13  # 19
    SET_QUANTITY = 0x15  # 21
    GET_PRINT_STATUS = 0xA3  # 163


class NiimbotPacket:
    """Niimbot communication packet with NiimPrintX protocol"""
    
    def __init__(self, type_: int, data: bytes = b""):
        self.type = type_
        self.data = data

    def to_bytes(self) -> bytes:
        """Convert packet to bytes for transmission with correct checksum"""
        checksum = self.type ^ len(self.data)
        for i in self.data:
            checksum ^= i
        return bytes([0x55, 0x55, self.type, len(self.data), *self.data, checksum, 0xAA, 0xAA])

    @staticmethod
    def from_bytes(data: bytes) -> Optional['NiimbotPacket']:
        """Parse packet from received bytes"""
        if len(data) < 7 or data[0:2] != b'\x55\x55' or data[-2:] != b'\xAA\xAA':
            logger.warning(f"Invalid packet format: {data.hex()}")
            return None
            
        type_ = data[2]
        len_ = data[3]
        
        if len(data) < 7 + len_:
            logger.warning(f"Packet too short: expected {7 + len_}, got {len(data)}")
            return None
            
        packet_data = data[4:4+len_]
        checksum_received = data[4+len_]
        
        # Verify checksum
        checksum = type_ ^ len_
        for i in packet_data:
            checksum ^= i
            
        if checksum != checksum_received:
            logger.warning(f"Checksum mismatch: expected 0x{checksum:02x}, got 0x{checksum_received:02x}")
            return None
            
        return NiimbotPacket(type_, packet_data)


def packet_to_int(packet: NiimbotPacket) -> int:
    """Convert packet data to integer"""
    if not packet.data:
        return 0
    return int.from_bytes(packet.data, byteorder='big')


class NiimbotPrinterBLE:
    """Niimbot printer client for BLE communication"""

    # Working characteristic UUID for both B1 and D110
    # This UUID supports read, write, and notify operations
    CHAR_UUID = "bef8d6c9-9c21-4c9e-b632-bd58c1009f9f"
    
    # Known printer models and their addresses (can be configured)
    KNOWN_PRINTERS = {
        "B1": "13:07:12:A6:40:07",
        "D110": "C3:33:D5:02:36:62"
    }

    def __init__(self, address: str, model: str = "d110"):
        """
        Initialize Niimbot BLE printer client
        
        Args:
            address: Bluetooth device address (MAC) or printer model name
            model: Printer model (b1, d110, etc.)
        """
        # Handle model name as address
        self.address = self.KNOWN_PRINTERS.get(address.upper(), address)
        self.model = model.lower()
        self.client: Optional[BleakClient] = None
        self.connected = False
        self._response_queue: asyncio.Queue = asyncio.Queue()
        self._notification_handler_registered = False

    async def connect(self) -> bool:
        """
        Connect to the printer via BLE
        
        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"Connecting to Niimbot {self.model.upper()} at {self.address}...")
            
            # Create BLE client
            self.client = BleakClient(self.address)
            await self.client.connect()
            
            if not self.client.is_connected:
                logger.error("Failed to connect to printer")
                return False
            
            # Start listening for notifications
            await self.client.start_notify(self.CHAR_UUID, self._notification_handler)
            self._notification_handler_registered = True
            
            self.connected = True
            logger.info(f"✅ Connected to {self.model.upper()} printer")
            
            # Send heartbeat to verify connection
            response = await self.send_heartbeat()
            if response:
                logger.info("Printer is responsive")
                return True
            else:
                logger.warning("Printer connected but not responding to heartbeat")
                return True  # Still return True as we are connected
                
        except Exception as e:
            logger.error(f"Failed to connect to printer: {e}")
            self.connected = False
            return False

    def _notification_handler(self, sender, data: bytearray):
        """Handle incoming BLE notifications from printer"""
        try:
            logger.debug(f"📨 Received {len(data)} bytes: {data.hex()}")
            packet = NiimbotPacket.from_bytes(bytes(data))
            if packet:
                self._response_queue.put_nowait(packet)
            else:
                logger.warning(f"Failed to parse packet: {data.hex()}")
        except Exception as e:
            logger.error(f"Error in notification handler: {e}")

    async def _send_packet(self, packet: NiimbotPacket, wait_response: bool = True) -> Optional[NiimbotPacket]:
        """
        Send a packet to the printer and optionally wait for response
        
        Args:
            packet: Packet to send
            wait_response: Whether to wait for a response (default True)
            
        Returns:
            Response packet or None if timeout/no wait
        """
        if not self.client or not self.connected:
            logger.error("Printer not connected")
            return None

        try:
            # Clear any old responses
            while not self._response_queue.empty():
                try:
                    self._response_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            # Send packet
            packet_bytes = packet.to_bytes()
            logger.debug(f"📤 Sending: {packet_bytes.hex()}")
            await self.client.write_gatt_char(self.CHAR_UUID, packet_bytes)

            # Wait for response with timeout if requested
            if wait_response:
                try:
                    response = await asyncio.wait_for(
                        self._response_queue.get(),
                        timeout=3.0
                    )
                    logger.debug(f"✅ Got response: type=0x{response.type:02x}, data={response.data.hex()}")
                    return response
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for response to command 0x{packet.type:02x}")
                    return None
            else:
                # Small delay to let the printer process
                await asyncio.sleep(0.01)
                return None

        except Exception as e:
            logger.error(f"Error sending packet: {e}")
            return None

    async def send_heartbeat(self) -> Optional[NiimbotPacket]:
        """Send heartbeat to printer"""
        packet = NiimbotPacket(RequestCodeEnum.HEARTBEAT, b'\x01')
        return await self._send_packet(packet)

    async def get_info(self, key: InfoEnum) -> Optional[int]:
        """
        Get printer information
        
        Args:
            key: Information type to request
            
        Returns:
            Information value or None
        """
        packet = NiimbotPacket(RequestCodeEnum.GET_INFO, bytes([key]))
        response = await self._send_packet(packet)
        
        if response and response.data:
            return packet_to_int(response)
        return None

    async def get_rfid(self) -> Optional[Dict]:
        """
        Get RFID tag information from loaded label
        
        Returns:
            Dict with RFID info or None
        """
        packet = NiimbotPacket(RequestCodeEnum.GET_RFID, b'\x01')
        response = await self._send_packet(packet)
        
        if response and len(response.data) >= 16:
            try:
                # Parse RFID response
                data = response.data
                return {
                    'uuid': data[0:8].hex(),
                    'barcode': data[8:16].decode('ascii', errors='ignore').strip('\x00'),
                    'serial': data[16:32].decode('ascii', errors='ignore').strip('\x00') if len(data) >= 32 else None,
                    'total_len': int.from_bytes(data[32:34], 'big') if len(data) >= 34 else None,
                    'used_len': int.from_bytes(data[34:36], 'big') if len(data) >= 36 else None,
                    'type': data[36] if len(data) > 36 else None
                }
            except Exception as e:
                logger.error(f"Error parsing RFID data: {e}")
                return None
        return None

    async def set_label_type(self, label_type: int) -> bool:
        """Set label type"""
        packet = NiimbotPacket(RequestCodeEnum.SET_LABEL_TYPE, bytes([label_type]))
        response = await self._send_packet(packet)
        return response is not None

    async def set_label_density(self, density: int) -> bool:
        """Set print density (1-5, 3 is default)"""
        if not 1 <= density <= 5:
            density = 3
        packet = NiimbotPacket(RequestCodeEnum.SET_LABEL_DENSITY, bytes([density]))
        response = await self._send_packet(packet)
        return response is not None

    async def start_print(self, total_pages: int = 1) -> bool:
        """
        Start print job (model-specific)
        
        Args:
            total_pages: Total number of pages to print
            
        Returns:
            bool: True if successful
        """
        if self.model == "b1":
            # B1: 7-byte format [totalPages(u16), 0x00, 0x00, 0x00, 0x00, pageColor(u8)]
            data = struct.pack(">H5B", total_pages, 0, 0, 0, 0, 0)
        else:
            # D110: 1-byte format (standard)
            data = b'\x01'
            
        packet = NiimbotPacket(RequestCodeEnum.START_PRINT, data)
        response = await self._send_packet(packet)
        return response is not None

    async def end_print(self) -> bool:
        """End print job (no payload for B1, standard for D110)"""
        # B1 and D110 both use empty payload for PrintEnd
        packet = NiimbotPacket(RequestCodeEnum.END_PRINT, b'')
        response = await self._send_packet(packet)
        return response is not None

    async def start_page_print(self) -> bool:
        """Start printing a page"""
        packet = NiimbotPacket(RequestCodeEnum.START_PAGE_PRINT, b'\x01')
        response = await self._send_packet(packet)
        return response is not None

    async def end_page_print(self) -> bool:
        """End printing a page"""
        packet = NiimbotPacket(RequestCodeEnum.END_PAGE_PRINT, b'\x01')
        response = await self._send_packet(packet)
        return response is not None

    async def allow_print_clear(self) -> bool:
        """Allow print and clear buffer (D110 only, not used by B1)"""
        packet = NiimbotPacket(RequestCodeEnum.ALLOW_PRINT_CLEAR, b'\x01')
        response = await self._send_packet(packet)
        return response is not None

    async def set_dimension(self, width: int, height: int, quantity: int = 1) -> bool:
        """
        Set label dimensions
        
        Note: Despite parameter names, this follows NiimPrintX convention where:
        - First parameter = image.height 
        - Second parameter = image.width
        So when calling, pass: set_dimension(height, width)
        
        Args:
            width: First dimension (should be image HEIGHT)
            height: Second dimension (should be image WIDTH)
            quantity: Number of copies (B1 only)
            
        Returns:
            bool: True if successful
        """
        if self.model == "b1":
            # B1: 6-byte format - pack as provided
            data = struct.pack('>HHH', width, height, quantity)
        else:
            # D110: 4-byte format - pack as provided
            data = struct.pack('>HH', width, height)
            
        packet = NiimbotPacket(RequestCodeEnum.SET_DIMENSION, data)
        response = await self._send_packet(packet)
        return response is not None

    async def set_quantity(self, quantity: int) -> bool:
        """Set number of copies to print"""
        data = struct.pack('>H', quantity)
        packet = NiimbotPacket(RequestCodeEnum.SET_QUANTITY, data)
        response = await self._send_packet(packet)
        return response is not None

    async def get_print_status(self) -> Optional[Dict]:
        """
        Get current print status
        
        Returns:
            Dict with status info: {page, print_progress, feed_progress}
        """
        packet = NiimbotPacket(RequestCodeEnum.GET_PRINT_STATUS, b'')
        response = await self._send_packet(packet)
        
        if response and len(response.data) >= 4:
            # Parse: page(i16), pagePrintProgress(i8), pageFeedProgress(i8)
            page = struct.unpack(">h", response.data[0:2])[0]
            print_progress = response.data[2]
            feed_progress = response.data[3]
            
            return {
                'page': page,
                'print_progress': print_progress,
                'feed_progress': feed_progress
            }
        return None

    async def print_image(self, image: Image.Image, density: int = 3, quantity: int = 1) -> bool:
        """
        Print an image to the label (model-specific)
        
        Args:
            image: PIL Image object
            density: Print density (1-5)
            quantity: Number of copies
            
        Returns:
            bool: True if print successful
        """
        try:
            logger.info(f"Starting {self.model.upper()} print job: {image.size}, density={density}, quantity={quantity}")
            
            # Prepare image (same as niimprint library)
            logger.info(f"Input image mode: {image.mode}, size: {image.size}")
            
            # Convert to grayscale and 1-bit
            # B1 doesn't need inversion (preview is already correct)
            # D110 needs inversion
            if self.model == "b1":
                # B1: Direct conversion without inversion
                image = image.convert('L').convert('1')
                logger.info(f"B1: Converted to 1-bit without inversion")
            else:
                # D110: Niimprint does: ImageOps.invert(image.convert('L')).convert('1')
                image = ImageOps.invert(image.convert('L')).convert('1')
                logger.info(f"D110: Inverted and converted to 1-bit")
            
            # Debug: Save the image to see what we're sending
            try:
                image.save('/tmp/debug_label.png')
                logger.info("Debug: Saved processed image to /tmp/debug_label.png")
            except Exception as e:
                logger.warning(f"Could not save debug image: {e}")
            
            width, height = image.size
            bytes_per_line = width // 8
            
            # ==================== INIT ====================
            logger.info("Setting label type and density...")
            if not await self.set_label_type(1):  # 1 = with gaps
                logger.error("Failed to set label type")
                return False
                
            if not await self.set_label_density(density):
                logger.error("Failed to set density")
                return False
            
            # Model-specific start print
            logger.info(f"Starting print ({self.model} protocol)...")
            if not await self.start_print(total_pages=quantity):
                logger.error("Failed to start print")
                return False
            
            # ==================== PAGE(S) ====================
            if self.model == "b1":
                # B1: Single page with quantity in SetPageSize
                if not await self._print_page_b1(image, width, height, bytes_per_line, quantity):
                    return False
            else:
                # D110: Use PrintClear and SetQuantity
                if not await self._print_page_d110(image, width, height, bytes_per_line, quantity):
                    return False
            
            # ==================== WAIT FOR FINISH ====================
            logger.info("Waiting for print to complete...")
            if self.model == "b1":
                # B1: Poll print status
                if not await self._wait_finished_b1(quantity):
                    return False
            else:
                # D110: Poll print status (same for D110)
                if not await self._wait_finished_d110(quantity):
                    return False
            
            # ==================== END ====================
            logger.info("Ending print job...")
            if not await self.end_print():
                logger.error("Failed to end print")
                return False
            
            logger.info("✅ Print job completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Print failed: {e}")
            return False

    async def _print_page_b1(self, image: Image.Image, width: int, height: int, bytes_per_line: int, quantity: int) -> bool:
        """Print page using B1 protocol"""
        try:
            # PageStart
            if not await self.start_page_print():
                logger.error("Failed to start page")
                return False
            
            # SetPageSize with quantity (6 bytes)
            # NiimPrintX calls: set_dimension(image.height, image.width)
            if not await self.set_dimension(height, width, quantity):
                logger.error("Failed to set dimensions")
                return False
            
            # Send bitmap data
            await self._send_bitmap_data(image, width, height, bytes_per_line)
            
            # PageEnd
            if not await self.end_page_print():
                logger.error("Failed to end page")
                return False
                
            return True
        except Exception as e:
            logger.error(f"B1 page print failed: {e}")
            return False

    async def _print_page_d110(self, image: Image.Image, width: int, height: int, bytes_per_line: int, quantity: int) -> bool:
        """Print page using D110 protocol"""
        try:
            # PrintClear
            if not await self.allow_print_clear():
                logger.error("Failed to clear print buffer")
                return False
            
            # PageStart
            if not await self.start_page_print():
                logger.error("Failed to start page")
                return False
            
            # SetPageSize (4 bytes)
            # NiimPrintX calls: set_dimension(image.height, image.width)
            if not await self.set_dimension(height, width):
                logger.error("Failed to set dimensions")
                return False
            
            # SetQuantity
            if not await self.set_quantity(quantity):
                logger.error("Failed to set quantity")
                return False
            
            # Send bitmap data
            await self._send_bitmap_data(image, width, height, bytes_per_line)
            
            # PageEnd
            if not await self.end_page_print():
                logger.error("Failed to end page")
                return False
                
            return True
        except Exception as e:
            logger.error(f"D110 page print failed: {e}")
            return False

    async def _send_bitmap_data(self, image: Image.Image, width: int, height: int, bytes_per_line: int):
        """Send bitmap data line by line"""
        logger.info(f"Sending {height} bitmap rows...")
        
        for y in range(height):
            # Convert line to bytes
            line_bytes = bytearray()
            for x in range(width):
                if x % 8 == 0:
                    line_bytes.append(0)
                pixel = image.getpixel((x, y))
                if pixel == 0:  # Black pixel
                    line_bytes[-1] |= (1 << (7 - (x % 8)))
            
            # Calculate bit counts for 3 segments
            seg_size = bytes_per_line // 3
            count1 = int.from_bytes(bytes(line_bytes[0:seg_size]), 'big').bit_count()
            count2 = int.from_bytes(bytes(line_bytes[seg_size:seg_size*2]), 'big').bit_count()
            count3 = int.from_bytes(bytes(line_bytes[seg_size*2:]), 'big').bit_count()
            
            # Build header: pos(u16), count1(u8), count2(u8), count3(u8), repeats(u8)
            header = struct.pack(">H3BB", y, count1, count2, count3, 1)
            
            # Send (0x85 = PrintBitmapRow)
            packet = NiimbotPacket(0x85, header + bytes(line_bytes))
            await self._send_packet(packet, wait_response=False)
            
            if y % 20 == 0:
                logger.info(f"Progress: {y}/{height} lines ({100*y//height}%)")
        
        logger.info(f"Progress: {height}/{height} lines (100%)")

    async def _wait_finished_b1(self, total_pages: int, timeout: float = 10.0, poll_interval: float = 0.3) -> bool:
        """Wait for B1 print to finish using status polling"""
        polls = int(timeout / poll_interval)
        
        for i in range(polls):
            status = await self.get_print_status()
            
            if status:
                page = status['page']
                print_prog = status['print_progress']
                feed_prog = status['feed_progress']
                
                logger.debug(f"Status: page={page}/{total_pages}, print={print_prog}%, feed={feed_prog}%")
                
                if page == total_pages and print_prog == 100 and feed_prog == 100:
                    logger.info("Print completed!")
                    return True
            
            await asyncio.sleep(poll_interval)
        
        logger.warning("Timeout waiting for print to complete")
        return False

    async def _wait_finished_d110(self, total_pages: int, timeout: float = 10.0, poll_interval: float = 0.3) -> bool:
        """Wait for D110 print to finish using status polling"""
        # D110 uses same status polling as B1
        return await self._wait_finished_b1(total_pages, timeout, poll_interval)

    async def disconnect(self):
        """Disconnect from printer"""
        if self.client:
            try:
                if self._notification_handler_registered:
                    await self.client.stop_notify(self.CHAR_UUID)
                    self._notification_handler_registered = False
                    
                if self.client.is_connected:
                    await self.client.disconnect()
                    
                logger.info("Disconnected from printer")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.connected = False
                self.client = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


async def scan_printers(timeout: float = 5.0) -> List[Dict]:
    """
    Scan for available Niimbot printers
    
    Args:
        timeout: Scan timeout in seconds
        
    Returns:
        List of dicts with 'address', 'name', and 'model' keys
    """
    logger.info(f"Scanning for Niimbot printers (timeout={timeout}s)...")
    
    devices = await BleakScanner.discover(timeout=timeout)
    printers = []
    
    for device in devices:
        name = device.name or ""
        if "B1" in name or "D110" in name or "Niimbot" in name.upper():
            model = "b1" if "B1" in name else "d110" if "D110" in name else "unknown"
            printers.append({
                'address': device.address,
                'name': name,
                'model': model
            })
            logger.info(f"Found: {name} ({device.address})")
    
    logger.info(f"Found {len(printers)} Niimbot printer(s)")
    return printers


# Alias for backwards compatibility
discover_niimbot_printers = scan_printers
