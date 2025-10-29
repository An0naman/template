# Niimbot B1 Printer BLE Implementation - SUCCESS

## Overview
Successfully implemented Bluetooth Low Energy (BLE) printing support for Niimbot B1 and D110 printers with model-specific protocol handling.

## Problem
- Initial implementation used standard NiimPrintX protocol
- Commands were accepted but **B1 printer did not physically print**
- Official Niimbot app printed immediately without button press

## Root Cause Discovery
Through research of the [niimbluelib](https://github.com/MultiMote/niimbluelib) TypeScript library, discovered that:

1. **B1 uses a different protocol variant than D110**
2. **Key differences in packet formats:**

### B1-Specific Commands (Different from Standard)

| Command | Standard | B1 Format | Notes |
|---------|----------|-----------|-------|
| PrintStart (0x01) | 1 byte | **7 bytes** | `[totalPages(u16), 0x00, 0x00, 0x00, 0x00, pageColor(u8)]` |
| SetPageSize (0x13) | 4 bytes | **6 bytes** | `[rows(u16), cols(u16), copiesCount(u16)]` |
| PrintClear (0x20) | Used | **NOT USED** | B1 doesn't use this command |
| PrintEnd (0xF3) | With data | **NO DATA** | Empty payload |
| Status Check | PrintEnd retry | **PrintStatus (0xA3) polling** | Active status polling |

## Solution Implementation

### 1. Model Detection
```python
def __init__(self, address: str, model: str = "d110"):
    self.model = model.lower()  # "b1" or "d110"
```

### 2. PrintStart (0x01) - Model-Specific
```python
async def start_print(self, total_pages: int = 1) -> bool:
    if self.model == "b1":
        # B1: 7-byte format
        data = struct.pack(">H5B", total_pages, 0, 0, 0, 0, 0)
    else:
        # D110: 1-byte format
        data = b'\x01'
    
    packet = NiimbotPacket(RequestCodeEnum.START_PRINT, data)
    return await self._send_packet(packet)
```

### 3. SetPageSize (0x13) - Model-Specific
```python
async def set_dimension(self, width: int, height: int, quantity: int = 1) -> bool:
    if self.model == "b1":
        # B1: 6-byte format with quantity
        data = struct.pack('>HHH', height, width, quantity)
    else:
        # D110: 4-byte format
        data = struct.pack('>HH', height, width)
    
    packet = NiimbotPacket(RequestCodeEnum.SET_DIMENSION, data)
    return await self._send_packet(packet)
```

### 4. Print Sequence - B1
```python
async def _print_page_b1(self, image, width, height, bytes_per_line, quantity):
    # 1. PageStart (0x03)
    await self.start_page_print()
    
    # 2. SetPageSize - 6 bytes with quantity
    await self.set_dimension(width, height, quantity)
    
    # 3. Send bitmap data (0x85)
    await self._send_bitmap_data(image, width, height, bytes_per_line)
    
    # 4. PageEnd (0xE3)
    await self.end_page_print()
```

### 5. Print Sequence - D110
```python
async def _print_page_d110(self, image, width, height, bytes_per_line, quantity):
    # 1. PrintClear (0x20)
    await self.allow_print_clear()
    
    # 2. PageStart (0x03)
    await self.start_page_print()
    
    # 3. SetPageSize - 4 bytes
    await self.set_dimension(width, height)
    
    # 4. SetQuantity (0x15)
    await self.set_quantity(quantity)
    
    # 5. Send bitmap data (0x85)
    await self._send_bitmap_data(image, width, height, bytes_per_line)
    
    # 6. PageEnd (0xE3)
    await self.end_page_print()
```

### 6. Status Polling
```python
async def _wait_finished_b1(self, total_pages: int, timeout: float = 10.0):
    for i in range(int(timeout / 0.3)):
        status = await self.get_print_status()  # PrintStatus (0xA3)
        
        if status:
            page = status['page']
            print_progress = status['print_progress']
            feed_progress = status['feed_progress']
            
            if page == total_pages and print_progress == 100 and feed_progress == 100:
                return True
        
        await asyncio.sleep(0.3)
```

## Test Results

### Before Fix
```
✅ Connected
📋 Commands sent: SetDensity, SetLabelType, PrintStart, etc.
✅ All commands accepted
❌ Nothing printed
```

### After Fix (B1-Specific Protocol)
```
✅ Connected to B1
🖨️  Starting B1 print job: (384, 50), density=3, quantity=1
⏳ Status polling:
   Poll 2: page=0/1, print=10%, feed=0%
   Poll 3: page=0/1, print=100%, feed=3%
   Poll 4: page=0/1, print=100%, feed=52%
   Poll 5: page=1/1, print=100%, feed=100%
   ✅ Print complete!
✅ Print job completed successfully
```

**Result: ✅ B1 PHYSICALLY PRINTED THE LABEL**

## Key Findings

1. **B1 is a newer model (2024)** with enhanced protocol
2. **Different models need different print tasks:**
   - D11_V1: Old format with page index
   - D110: Standard format with status polling
   - B1: Enhanced format with 7-byte PrintStart
   - B21_V1: Uses PrintEnd polling
   - D110M_V4: 9-byte PrintStart variant

3. **Critical B1 requirements:**
   - Must use 7-byte PrintStart
   - Must use 6-byte SetPageSize with copies
   - Must NOT use PrintClear
   - Must use active PrintStatus polling
   - PrintEnd has empty payload

## Files Modified

1. **app/services/niimbot_printer_ble.py**
   - Added model detection (`"b1"` vs `"d110"`)
   - Model-specific `start_print()` with 7-byte B1 format
   - Model-specific `set_dimension()` with 6-byte B1 format
   - Separate `_print_page_b1()` and `_print_page_d110()` methods
   - Status polling with proper response parsing
   - Fixed PrintEnd to use empty payload

2. **Test Scripts Created**
   - `test_b1_specific.py` - Initial B1-specific sequence test
   - `test_b1_correct_status.py` - Fixed status polling test ✅ SUCCESS
   - `test_updated_service.py` - Service integration test ✅ SUCCESS

## Usage

```python
from app.services.niimbot_printer_ble import NiimbotPrinterBLE
from PIL import Image

# For B1
async with NiimbotPrinterBLE("B1", model="b1") as printer:
    success = await printer.print_image(image, density=3, quantity=1)

# For D110
async with NiimbotPrinterBLE("D110", model="d110") as printer:
    success = await printer.print_image(image, density=3, quantity=1)
```

## References

- **niimbluelib**: https://github.com/MultiMote/niimbluelib
  - B1PrintTask: `/src/print_tasks/B1PrintTask.ts`
  - Print tasks docs: `/docs/documents/niimbot_print_tasks.md`
- **Working BLE Characteristic**: `bef8d6c9-9c21-4c9e-b632-bd58c1009f9f`

## Next Steps

1. ✅ B1 printing working
2. ✅ D110 protocol documented
3. ⬜ Test D110 physical printing
4. ⬜ Add web interface integration
5. ⬜ Support additional models (B21, D110M_V4, etc.)

---

**Status: ✅ B1 PRINTING SUCCESSFULLY IMPLEMENTED**
**Date: 2025-10-24**
