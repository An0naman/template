"""
Niimbot Printer Service
Handles Bluetooth connectivity and printing to Niimbot label printers (B1, D110)
Uses RFCOMM (Classic Bluetooth) instead of BLE
Based on the niimprint library protocol
"""

import logging
import struct
import math
import socket
import time
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
        self.sock: Optional[socket.socket] = None
        self.packet_buffer = bytearray()

    def connect(self, retries: int = 3) -> bool:
        """
        Connect to the printer using RFCOMM
        
        Args:
            retries: Number of connection attempts
        """
        for attempt in range(retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{retries} to {self.address}")
                
                self.sock = socket.socket(
                    socket.AF_BLUETOOTH,
                    socket.SOCK_STREAM,
                    socket.BTPROTO_RFCOMM
                )
                self.sock.settimeout(10.0)
                self.sock.connect((self.address, 1))  # RFCOMM channel 1
                
                logger.info(f"✅ Successfully connected to Niimbot printer at {self.address}")
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                    self.sock = None
                
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                logger.error(f"Failed to connect after {retries} attempts")
                return False
        
        return False

    def disconnect(self):
        """Disconnect from the printer"""
        if self.sock:
            try:
                self.sock.close()
                logger.info("Disconnected from printer")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.sock = None

    def _recv_packets(self) -> List[NiimbotPacket]:
        """Receive and parse packets from printer"""
        packets = []
        try:
            data = self.sock.recv(1024)
            if data:
                self.packet_buffer.extend(data)
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
            return packets
        
        # Parse complete packets from buffer
        while len(self.packet_buffer) > 4:
            pkt_len = self.packet_buffer[3] + 7
            if len(self.packet_buffer) >= pkt_len:
                packet = NiimbotPacket.from_bytes(self.packet_buffer[:pkt_len])
                if packet:
                    packets.append(packet)
                del self.packet_buffer[:pkt_len]
            else:
                break
        
        return packets

    def _send_packet(self, packet: NiimbotPacket):
        """Send packet to printer"""
        data = packet.to_bytes()
        self.sock.send(data)
        logger.debug(f"Sent packet type 0x{packet.type:02x}, length {len(packet.data)}")

    def _transceive(self, request_code: RequestCodeEnum, data: bytes = b"", resp_offset: int = 1) -> Optional[NiimbotPacket]:
        """Send command and wait for response"""
        resp_code = resp_offset + request_code
        packet = NiimbotPacket(request_code, data)
        
        self._send_packet(packet)
        
        # Wait for response
        for _ in range(6):
            packets = self._recv_packets()
            for pkt in packets:
                if pkt.type == 219:
                    raise ValueError("Printer returned error code 219")
                elif pkt.type == 0:
                    raise NotImplementedError("Command not implemented by printer")
                elif pkt.type == resp_code:
                    return pkt
            time.sleep(0.1)
        
        logger.warning(f"No response for command 0x{request_code:02x}")
        return None

    def get_info(self, key: InfoEnum) -> Optional[any]:
        """Get printer information"""
        response = self._transceive(RequestCodeEnum.GET_INFO, bytes((key,)))
        if not response:
            return None
            
        if key == InfoEnum.DEVICESERIAL:
            return response.data.hex()
        elif key in (InfoEnum.SOFTVERSION, InfoEnum.HARDVERSION):
            return packet_to_int(response) / 100
        else:
            return packet_to_int(response)

    def heartbeat(self) -> Dict:
        """Send heartbeat to printer"""
        response = self._transceive(RequestCodeEnum.HEARTBEAT, b"\x01")
        if not response:
            return {}
        
        result = {}
        if len(response.data) >= 13:
            result = {
                'closingState': response.data[9],
                'powerLevel': response.data[10],
                'paperState': response.data[11],
                'rfidReadState': response.data[12],
            }
        return result

    def set_label_type(self, n: int = 1) -> bool:
        """Set label type (1-3)"""
        assert 1 <= n <= 3
        response = self._transceive(RequestCodeEnum.SET_LABEL_TYPE, bytes((n,)), 16)
        return response and bool(response.data[0]) if response else False

    def set_label_density(self, n: int = 3) -> bool:
        """Set print density (1-5)"""
        assert 1 <= n <= 5
        response = self._transceive(RequestCodeEnum.SET_LABEL_DENSITY, bytes((n,)), 16)
        return response and bool(response.data[0]) if response else False

    def start_print(self) -> bool:
        """Start print job"""
        response = self._transceive(RequestCodeEnum.START_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    def end_print(self) -> bool:
        """End print job"""
        response = self._transceive(RequestCodeEnum.END_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    def start_page_print(self) -> bool:
        """Start page print"""
        response = self._transceive(RequestCodeEnum.START_PAGE_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    def end_page_print(self) -> bool:
        """End page print"""
        response = self._transceive(RequestCodeEnum.END_PAGE_PRINT, b"\x01")
        return response and bool(response.data[0]) if response else False

    def set_dimension(self, width: int, height: int) -> bool:
        """Set print dimensions"""
        response = self._transceive(RequestCodeEnum.SET_DIMENSION, struct.pack(">HH", width, height))
        return response and bool(response.data[0]) if response else False

    def set_quantity(self, n: int) -> bool:
        """Set print quantity"""
        response = self._transceive(RequestCodeEnum.SET_QUANTITY, struct.pack(">H", n))
        return response and bool(response.data[0]) if response else False

    def get_print_status(self) -> Dict:
        """Get current print status"""
        response = self._transceive(RequestCodeEnum.GET_PRINT_STATUS, b"\x01", 16)
        if not response or len(response.data) < 4:
            return {}
        
        try:
            page, progress1, progress2 = struct.unpack(">HBB", response.data)
            return {"page": page, "progress1": progress1, "progress2": progress2}
        except Exception as e:
            logger.error(f"Error parsing print status: {e}")
            return {}

    def _encode_image(self, image: Image):
        """Encode image for printing"""
        # Convert to monochrome
        img = ImageOps.invert(image.convert("L")).convert("1")

        # Yield packets for each line
        for y in range(img.height):
            line_data = [img.getpixel((x, y)) for x in range(img.width)]
            line_data = "".join("0" if pix == 0 else "1" for pix in line_data)
            line_data = int(line_data, 2).to_bytes(math.ceil(img.width / 8), "big")
            
            counts = (0, 0, 0)
            header = struct.pack(">H3BB", y, *counts, 1)
            yield NiimbotPacket(0x85, header + line_data)

    def print_image(self, image: Image, density: int = 3, quantity: int = 1) -> bool:
        """
        Print an image to the label printer
        
        Args:
            image: PIL Image to print
            density: Print density (1-5)
            quantity: Number of copies to print
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting print job: density={density}, quantity={quantity}")
            
            self.set_label_density(density)
            self.set_label_type(1)
            self.start_print()
            self.start_page_print()
            self.set_dimension(image.height, image.width)
            # self.set_quantity(quantity)  # Some models don't support this

            # Send image data
            for packet in self._encode_image(image):
                self._send_packet(packet)

            self.end_page_print()
            time.sleep(0.3)
            
            # Wait for print to complete
            while not self.end_print():
                time.sleep(0.1)

            logger.info("Print job completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during print: {e}", exc_info=True)
            try:
                self.end_print()
            except:
                pass
            return False


def discover_niimbot_printers(timeout: float = 10.0) -> List[Dict]:
    """
    Discover Niimbot printers via Bluetooth
    Note: Classic Bluetooth discovery requires system-level tools
    
    Args:
        timeout: Scan timeout in seconds
        
    Returns:
        List of discovered printers with name and address
    """
    logger.warning("Bluetooth discovery not implemented for RFCOMM. Use system Bluetooth tools to find printer address.")
    return []
