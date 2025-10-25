# Flask App Integration - Niimbot BLE Printing

## Overview
Your Flask application is now integrated with the working Niimbot BLE printer service!

## What Was Updated

### 1. API Endpoints (app/api/labels_api.py)
Updated three endpoints to use the new BLE service:

```python
# Before (old RFCOMM service - didn't work):
from ..services.niimbot_printer import NiimbotPrinter

# After (new BLE service - WORKS!):
from ..services.niimbot_printer_ble import NiimbotPrinterBLE as NiimbotPrinter
```

**Updated Endpoints:**
1. `GET /api/niimbot/discover` - Discover available printers
2. `POST /api/niimbot/connect` - Test connection to a printer
3. `POST /api/entries/<entry_id>/niimbot/print` - Print a label

### 2. Service Files

**Working Services:**
- ✅ `app/services/niimbot_printer_ble.py` - **NEW** - BLE service with B1/D110 support
- ⚠️ `app/services/niimbot_printer.py` - Old RFCOMM service (can be removed)
- ⚠️ `app/services/niimbot_printer_rfcomm.py` - Old RFCOMM service (can be removed)

## How It Works Now

### 1. Printer Discovery
```bash
curl http://localhost:5000/api/niimbot/discover?timeout=5
```

Response:
```json
{
  "success": true,
  "printers": [
    {
      "address": "13:07:12:A6:40:07",
      "name": "B1",
      "model": "b1"
    },
    {
      "address": "C3:33:D5:02:36:62",
      "name": "D110",
      "model": "d110"
    }
  ],
  "count": 2
}
```

### 2. Test Connection
```bash
curl -X POST http://localhost:5000/api/niimbot/connect \
  -H "Content-Type: application/json" \
  -d '{
    "address": "B1",
    "model": "b1"
  }'
```

Response:
```json
{
  "success": true,
  "info": {
    "battery": 100,
    "connected": true
  }
}
```

### 3. Print a Label
```bash
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{
    "printer_address": "B1",
    "printer_model": "b1",
    "label_size": "50x14mm",
    "density": 3,
    "quantity": 1
  }'
```

Response:
```json
{
  "success": true,
  "message": "Successfully printed 1 label(s)",
  "entry_id": 1
}
```

## Frontend Integration

Your frontend can now call these endpoints to print labels directly to Niimbot printers!

### Example JavaScript:

```javascript
// 1. Discover printers
async function discoverPrinters() {
  const response = await fetch('/api/niimbot/discover?timeout=5');
  const data = await response.json();
  return data.printers;
}

// 2. Test connection
async function testConnection(address, model) {
  const response = await fetch('/api/niimbot/connect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address, model })
  });
  return await response.json();
}

// 3. Print label
async function printLabel(entryId, printerAddress, printerModel) {
  const response = await fetch(`/api/entries/${entryId}/niimbot/print`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      printer_address: printerAddress,
      printer_model: printerModel,
      label_size: '50x14mm',
      density: 3,
      quantity: 1
    })
  });
  return await response.json();
}

// Usage:
const printers = await discoverPrinters();
console.log('Found printers:', printers);

const result = await printLabel(1, 'B1', 'b1');
console.log('Print result:', result);
```

## Supported Printers

| Model | Address | Protocol | Status |
|-------|---------|----------|--------|
| B1 | 13:07:12:A6:40:07 | BLE (7-byte PrintStart) | ✅ **WORKING** |
| D110 | C3:33:D5:02:36:62 | BLE (4-byte SetPageSize) | ✅ Configured |

## Configuration

### Printer Addresses
The service supports both:
1. **Direct MAC addresses**: `"13:07:12:A6:40:07"`
2. **Model shortcuts**: `"B1"` or `"D110"`

```python
# Both work:
printer = NiimbotPrinterBLE("13:07:12:A6:40:07", model="b1")
printer = NiimbotPrinterBLE("B1", model="b1")  # Uses KNOWN_PRINTERS dict
```

### Label Configurations
Already configured in your app:

```python
LABEL_CONFIGS = {
    'niimbot_b1': {
        'name': 'Niimbot B1',
        'type': 'niimbot',
        'width': 384,    # pixels (50mm @ 203 DPI)
        'height': 108,   # pixels (14mm @ 203 DPI)
        # ... more config
    },
    'niimbot_d110': {
        'name': 'Niimbot D110',
        'type': 'niimbot',
        'width': 384,
        'height': 108,
        # ... more config
    }
}
```

## Testing

### Option 1: Using the Test Script
```bash
python test_api_integration.py
```

### Option 2: Direct API Testing
1. Start your Flask app:
   ```bash
   docker compose up
   ```

2. Test discovery:
   ```bash
   curl http://localhost:5000/api/niimbot/discover
   ```

3. Test printing:
   ```bash
   curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
     -H "Content-Type: application/json" \
     -d '{"printer_address": "B1", "printer_model": "b1", "density": 3, "quantity": 1}'
   ```

## Key Features

✅ **Model-Specific Protocol Support**
- B1: 7-byte PrintStart, 6-byte SetPageSize
- D110: Standard 1-byte PrintStart, 4-byte SetPageSize

✅ **Status Polling**
- Real-time print progress monitoring
- Reports: page, print_progress, feed_progress

✅ **Error Handling**
- Connection failures
- Print errors
- Timeout handling

✅ **Async Support**
- Non-blocking BLE operations
- Proper async/await integration with Flask

## Next Steps

1. ✅ **BLE service working** - B1 prints successfully
2. ✅ **API integration complete** - Endpoints updated
3. ⬜ **Frontend UI** - Add printer selection dropdown
4. ⬜ **Settings page** - Configure default printer
5. ⬜ **Test D110** - Verify D110 physical printing

## Troubleshooting

### "Bluetooth support not available"
Install dependencies:
```bash
pip install bleak>=0.21.0
```

### "Failed to connect to printer"
1. Check printer is powered on
2. Check Bluetooth is enabled
3. Check printer is paired (if required)
4. Try discovering first: `curl http://localhost:5000/api/niimbot/discover`

### "Print job failed"
1. Check printer has paper loaded
2. Check battery level
3. Check label size matches configuration
4. Try lower density (2 instead of 3)

## Summary

🎉 **Your app now supports direct Niimbot printing via Bluetooth!**

- API endpoints are ready to use
- B1 printer tested and working
- Frontend just needs to call the endpoints
- No more generating PDFs and manual printing for Niimbot labels!

---

**Status: ✅ FULLY INTEGRATED**
**Date: 2025-10-24**
