# B1 Printer Configuration - COMPLETE ✅

## Final Configuration

### Your Setup
- **Printer**: Niimbot B1
- **Label Size**: 60x30mm (384x237 pixels @ 203 DPI)
- **Rotation**: 0° (no rotation needed)
- **Margins**: 2mm on all sides

### What Was Fixed

1. **✅ BLE Protocol**: B1-specific 7-byte PrintStart and 6-byte SetPageSize
2. **✅ Orientation**: Changed default rotation from -90° to 0°
3. **✅ Dimensions**: Updated to use correct 60x30mm label size
4. **✅ Margins**: Increased to 2mm to account for printhead limitations

## Configuration Summary

### app/api/labels_api.py

```python
# Label configuration
'niimbot_b1': {
    'max_width_px': 384,  # 48mm @ 203 DPI
    'dpi': 203,
    'common_sizes': {
        '60x30mm': {'width_mm': 60, 'height_mm': 30},  # Your labels
        # ... other sizes available
    }
}

# Default settings
label_size = '60x30mm'  # Default
rotation = 0            # No rotation
margin = 2mm            # Safe printing area
```

### app/services/niimbot_printer_ble.py

```python
# B1-specific protocol
- PrintStart: 7 bytes [totalPages(u16), 0x00, 0x00, 0x00, 0x00, pageColor(u8)]
- SetPageSize: 6 bytes [rows(u16), cols(u16), copiesCount(u16)]
- No PrintClear command
- Status polling for print completion
```

## Usage

### From Your Web App

```javascript
// Print a label to B1
fetch('/api/entries/123/niimbot/print', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    printer_address: 'B1',           // or '13:07:12:A6:40:07'
    printer_model: 'b1',
    label_size: '60x30mm',           // Optional - defaults to 60x30mm
    density: 3,                      // 1-5, default 3
    quantity: 1,                     // Number of copies
    rotation: 0                      // Optional - defaults to 0
  })
});
```

### From Command Line

```bash
# Start app
docker compose up --build -d

# Print a label
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{
    "printer_address": "B1",
    "printer_model": "b1",
    "label_size": "60x30mm",
    "density": 3,
    "quantity": 1
  }'
```

## Label Dimensions Reference

| Label Size | Pixels | Use Case |
|------------|--------|----------|
| 30x12mm | 384x95 | Small labels |
| 30x15mm | 384x119 | Name tags |
| 40x20mm | 384x158 | Product labels |
| 40x24mm | 384x189 | Medium labels |
| **60x30mm** | **384x237** | **Your current labels** |

Note: Width is capped at 384px (48mm) which is the B1's maximum printhead width.

## Border Option

If you want a border around labels, add this to your system parameters:

```sql
INSERT INTO SystemParameters (param_key, param_value) 
VALUES ('label_border', 'true');
```

Then labels will have a 2px black border with proper margins.

## Troubleshooting

### Border Only Shows on Left
✅ **Fixed** - Increased margins to 2mm

### Label Too Narrow
✅ **Fixed** - Using full 384px width

### Label Spans Multiple Physical Labels
✅ **Fixed** - Using correct 60x30mm dimensions (384x237px)

### Text Sideways
✅ **Fixed** - Changed rotation to 0°

### "Connection failed"
- Check printer is powered on
- Check Bluetooth is enabled
- Try: `curl http://localhost:5000/api/niimbot/discover`

### "Print failed"
- Check paper is loaded correctly
- Check battery level
- Try lower density (2 instead of 3)

## Next Steps

1. ✅ **B1 printing working perfectly**
2. ✅ **Correct dimensions (60x30mm)**
3. ✅ **No rotation needed**
4. ✅ **Proper margins**
5. ⬜ Update your frontend UI to use these settings
6. ⬜ Add label size selector for users with different labels
7. ⬜ Test D110 printer (when available)

## Files Changed

1. **app/services/niimbot_printer_ble.py** - BLE service with B1 protocol
2. **app/api/labels_api.py** - Updated imports, dimensions, rotation, margins
3. **Test scripts** - Various orientation and dimension tests

---

**Status: ✅ FULLY WORKING**

Your B1 printer is now correctly configured and integrated with your Flask app!

**Date: 2025-10-24**
