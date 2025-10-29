# Label Printing System

Complete guide to the label printing system with support for A4 sheet labels and Niimbot thermal printers.

## Quick Start

### A4 Sheet Labels (Regular Printer)
1. Go to any entry's details page
2. Select label type: "8 Labels (2×4)" or "14 Labels (2×7)"
3. Click "Preview Label" → "Download PDF"
4. Print on A4 label sheets

### Niimbot Thermal Printers
1. Turn on printer (blue light = pairing mode)
2. Run: `./run_with_bluetooth.sh` (Bluetooth requires native mode)
3. Select "Niimbot B1" or "Niimbot D110"
4. Click "Discover Printers" → Select printer → "Print Label"

---

## Printer Types

### 1. A4 Sheet Labels (2×4) - 8 Labels per Sheet

**Specifications**:
- Paper: A4 (210mm × 297mm)
- Label Size: 97.5mm × 65.5mm (fixed)
- Layout: 2 columns × 4 rows
- Margins: Top/Bottom 10mm, Left/Right 5mm
- Gap: 5mm between labels

**Use Cases**: Address labels, large product labels

**Features**:
- QR codes with customizable prefix
- Logo placement (top-left, top-right, bottom-left, bottom-right)
- Border styles (simple, double, rounded)
- Text wrapping
- High-resolution PDF output (300 DPI)

### 2. A4 Sheet Labels (2×7) - 14 Labels per Sheet

**Specifications**:
- Paper: A4 (210mm × 297mm)
- Label Size: 97.5mm × 35.3mm (fixed)
- Layout: 2 columns × 7 rows
- Margins: Top/Bottom 10mm, Left/Right 5mm
- Gap: 5mm between labels

**Use Cases**: Mailing labels, smaller product labels

**Features**: Same as 8-label sheets, optimized for smaller height

### 3. Niimbot B1 (Bluetooth Thermal Printer)

**Specifications**:
- Type: Roll-fed thermal printer
- Max Width: 384px (48mm @ 203 DPI)
- Connection: Bluetooth BLE
- Print Method: Direct thermal (no ink required)

**Available Label Sizes**:
- **60mm × 30mm** - Large labels (default)
  - Font: 8pt body, 12pt title
  - QR Code: Medium, right position
  
- **40mm × 24mm** - Medium-large labels
  - Font: 8pt body, 11pt title
  - QR Code: Medium, right position
  
- **40mm × 20mm** - Medium labels
  - Font: 7pt body, 10pt title
  - QR Code: Small, right position
  
- **30mm × 15mm** - Small labels
  - Font: 7pt body, 10pt title
  - QR Code: Small, bottom-right position
  
- **30mm × 12mm** - Extra small labels
  - Font: 6pt body, 9pt title
  - No QR code (space limited)

**Features**:
- Auto-discovery via Bluetooth
- Adjustable print density (1-5, recommend 3)
- Multiple copies (1-10)
- Label preview before printing
- Automatic printer status check

### 4. Niimbot D110 (Wider Thermal Printer)

**Specifications**:
- Type: Roll-fed thermal printer
- Max Width: 576px (72mm @ 203 DPI)
- Connection: Bluetooth BLE

**Available Label Sizes**:
- **75mm × 12mm** - Wide labels
  - Font: 7pt body, 10pt title
  - No border (space optimized)
  - Optional small QR code

**Use Cases**: Cable labels, shelf labels, price tags

---

## Configuration

### Global Settings (Settings → Label Printing)

**General Settings**:
- Font sizes (body and title)
- QR code settings (prefix, size, position)
- Border style (simple, double, rounded, none)
- Logo settings (upload, position)
- Text wrapping (enable/disable)

**Per-Size Settings**:
Each label size can have independent settings:
- `label_60x30mm_font_size`
- `label_60x30mm_title_font_size`
- `label_60x30mm_border_style`
- `label_60x30mm_include_qr_code`
- `label_60x30mm_qr_size`
- (and similar for all other sizes)

**Rotation Settings**:
Labels can be rotated 90° for landscape orientation:
- `label_60x30mm_r90_*` settings for rotated labels

### Database Storage

All settings stored in `SystemParameters` table:
```sql
SELECT parameter_name, parameter_value 
FROM SystemParameters 
WHERE parameter_name LIKE 'label_%';
```

---

## Label Orientation & Rotation

### Portrait (Default)
```
┌─────────┐
│  Title  │
│ Content │
│   QR    │
└─────────┘
```

### Landscape (90° Rotation)
```
┌──────────────────┐
│ Title  Content  QR│
└──────────────────┘
```

**When to Rotate**:
- Wide labels (75×12mm)
- More horizontal space needed
- QR code + logo + text combination

**How to Enable**:
1. Go to Settings → Label Printing
2. Enable rotation for specific size
3. Adjust `_r90` settings independently

---

## Logo Integration

### Upload Logo
1. Go to Settings → System Configuration
2. Upload logo (PNG, JPG, GIF supported)
3. Recommended: 150×150px or smaller
4. Transparent background works best

### Logo Positions
- `top-left` - Above title (default)
- `top-right` - Opposite corner
- `bottom-left` - Below content
- `bottom-right` - Near QR code

### Per-Label Size Control
```
label_60x30mm_include_logo: true/false
label_60x30mm_logo_position: top-left
```

**Adaptive Layout**:
Logo automatically resizes based on:
- Label dimensions
- QR code presence
- Text content length

---

## QR Code Features

### QR Code Content
- Entry ID (e.g., `https://example.com/entries/42`)
- Customizable prefix in settings
- Automatic data encoding
- Error correction level: M (15% recovery)

### QR Code Sizes
- `small` - 50×50px (30mm labels)
- `medium` - 80×80px (40-60mm labels)
- `large` - 120×120px (rotated 60mm labels)

### QR Code Positions
- `right` - Right side of label (default)
- `bottom-right` - Lower corner
- `top-right` - Upper corner (rotated)

### Configuration
```
label_qr_code_prefix: https://myapp.example.com
label_60x30mm_include_qr_code: true
label_60x30mm_qr_size: medium
label_60x30mm_qr_position: right
```

---

## Text Wrapping

### Automatic Wrapping
Text automatically wraps based on:
- Label width
- Font size
- QR code/logo space

### Manual Control
```
label_text_wrap: true/false
```

**When to Disable**:
- Very small labels (30×12mm)
- Single-line titles only
- Space is critical

### Wrapping Behavior
- Title: Max 2 lines
- Description: Max 3-4 lines
- Truncation with "..." if exceeds

---

## Border Styles

### Available Styles

**Simple** (1px line):
```
┌─────────┐
│ Content │
└─────────┘
```

**Double** (2px line):
```
╔═════════╗
║ Content ║
╚═════════╝
```

**Rounded** (curved corners):
```
╭─────────╮
│ Content │
╰─────────╯
```

**None** (borderless):
```
  Content
```

### Recommendations
- **Simple**: General purpose, clean look
- **Double**: Important items, emphasis
- **Rounded**: Modern aesthetic
- **None**: Maximize space on small labels

---

## Niimbot Setup & Troubleshooting

### Initial Setup

1. **Pair Printer** (first time only):
```bash
bluetoothctl
scan on
# Wait for device to appear
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
exit
```

2. **Run Application**:
```bash
# Docker doesn't support Bluetooth well
docker compose down

# Run natively with Bluetooth
./run_with_bluetooth.sh
```

3. **Test Connection**:
- Go to entry page
- Click "Discover Printers"
- Should see your printer listed

### Common Issues

**Printer Not Discovered**:
- Check Bluetooth is enabled: `bluetoothctl show`
- Verify printer is on (blue light blinking)
- Unpair and re-pair: `bluetoothctl remove XX:XX:XX:XX:XX:XX`
- Restart Bluetooth: `sudo systemctl restart bluetooth`

**Print Quality Issues**:
- Adjust density (try 2-4)
- Check label alignment in printer
- Clean print head
- Ensure correct label size selected

**"Printer Busy" Error**:
- Wait 10 seconds and retry
- Power cycle printer
- Check no other device connected

**Docker Bluetooth Issues**:
- Docker containers have limited Bluetooth access
- Must run natively: `./run_with_bluetooth.sh`
- Alternative: Use USB-to-Bluetooth adapter

### Testing Without Printer

**Preview Mode**:
1. Select Niimbot printer type
2. Click "Preview Label"
3. See thermal-optimized rendering
4. Test different sizes and settings

**Print to PDF**:
- Select A4 label type instead
- Download PDF
- View what would print

---

## API Reference

### Generate Label Preview

**Endpoint**: `GET /api/labels/entry/<entry_id>/preview`

**Query Parameters**:
- `label_type` - "60x30mm", "40x20mm", etc.
- `printer_type` - "niimbot_b1", "niimbot_d110", "a4_8", "a4_14"
- `rotation` - "0" or "90"

**Response**: PNG image

### Print to Niimbot

**Endpoint**: `POST /api/labels/print_niimbot`

**Request Body**:
```json
{
  "entry_id": 42,
  "printer_address": "XX:XX:XX:XX:XX:XX",
  "label_size": "60x30mm",
  "density": 3,
  "quantity": 1,
  "printer_type": "b1"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Printed successfully"
}
```

### Discover Printers

**Endpoint**: `GET /api/labels/discover_printers`

**Query Parameters**:
- `printer_type` - "b1" or "d110"

**Response**:
```json
{
  "printers": [
    {
      "name": "B1_XXXX",
      "address": "XX:XX:XX:XX:XX:XX",
      "rssi": -65
    }
  ]
}
```

---

## Best Practices

### Label Design
1. **Keep titles short** - 3-5 words max
2. **Use QR codes for digital linking** - Set prefix to your app URL
3. **Test before bulk printing** - Preview first
4. **Match label size to use case** - Small labels for components, large for products

### Performance
1. **Batch A4 printing** - 8 or 14 labels at once
2. **Niimbot: Print multiple copies** - Faster than individual prints
3. **Cache label preview** - Reduce generation time

### Maintenance
1. **Clean thermal printhead** - Monthly for best quality
2. **Check Bluetooth pairing** - Re-pair if connection issues
3. **Update label settings** - Test new sizes in dev environment first

### Security
1. **QR code prefix** - Use HTTPS URLs
2. **Validate entry IDs** - Prevent unauthorized access
3. **Limit file uploads** - Logo files only from trusted sources

---

## Related Documentation

- [Niimbot Printer Integration](./NIIMBOT.md) - Detailed Bluetooth setup
- [Installation Guide](../setup/INSTALLATION.md) - System requirements
- [API Reference](../guides/API_REFERENCE.md) - Complete API docs

---

## Changelog

**v1.0** - Initial A4 sheet labels
**v1.1** - Added Niimbot B1 support
**v1.2** - Added Niimbot D110 support
**v1.3** - Logo integration and adaptive layouts
**v1.4** - Label rotation and landscape mode
**v1.5** - Per-size configuration system
