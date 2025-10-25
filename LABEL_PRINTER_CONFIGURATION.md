# Label Printer Configuration Guide

## Overview
The label printing system now supports different printer types with their specific label sizes. Settings are configured per printer type and label size for optimal results.

## Printer Types

### 1. **8 Labels (2x4) - A4 Sheet**
- **Type**: Static sheet labels for regular printers
- **Paper Size**: A4 (210mm × 297mm)
- **Label Size**: 97.5mm × 65.5mm (FIXED)
- **Layout**: 2 columns × 4 rows = 8 labels per sheet
- **Margins**: 
  - Top/Bottom: 10mm (1cm buffer)
  - Left/Right: 5mm
  - Gap between labels: 5mm (0.5cm padding)
- **Use Case**: Standard address labels, larger product labels
- **Settings**: Static - no size variations

### 2. **14 Labels (2x7) - A4 Sheet**
- **Type**: Static sheet labels for regular printers
- **Paper Size**: A4 (210mm × 297mm)
- **Label Size**: 97.5mm × 35.3mm (FIXED)
- **Layout**: 2 columns × 7 rows = 14 labels per sheet
- **Margins**: 
  - Top/Bottom: 10mm (1cm buffer)
  - Left/Right: 5mm
  - Gap between labels: 5mm (0.5cm padding)
- **Use Case**: Mailing labels, smaller product labels
- **Settings**: Static - no size variations

### 3. **Niimbot B1 (Bluetooth Thermal Printer)**
- **Type**: Roll-fed thermal printer
- **Max Width**: 384px (48mm @ 203 DPI)
- **Connection**: Bluetooth BLE
- **Available Label Sizes**:
  - **60mm × 30mm** - Large labels (default)
    - Font: 8pt body, 12pt title
    - Border: Simple
    - QR Code: Medium, right position
  - **40mm × 24mm** - Medium-large labels
    - Font: 8pt body, 11pt title
    - Border: Simple
    - QR Code: Medium, right position
  - **40mm × 20mm** - Medium labels
    - Font: 7pt body, 10pt title
    - Border: Simple
    - QR Code: Small, right position
  - **30mm × 15mm** - Small labels
    - Font: 7pt body, 10pt title
    - Border: Simple
    - QR Code: Small, bottom-right position
  - **30mm × 12mm** - Extra small labels
    - Font: 6pt body, 9pt title
    - Border: None
    - QR Code: Disabled by default
  - **Default** - Fallback for unlisted sizes

### 4. **Niimbot D110 (Bluetooth Thermal Printer)**
- **Type**: Roll-fed thermal printer
- **Max Width**: 240px (30mm @ 203 DPI)
- **Connection**: Bluetooth BLE
- **Available Label Sizes**:
  - **75mm × 12mm** - Extra wide labels
    - Font: 7pt body, 10pt title
    - Border: None
    - QR Code: Disabled by default
  - **50mm × 14mm** - Standard labels
    - Font: 7pt body, 10pt title
    - Border: None
    - QR Code: Disabled by default
  - **40mm × 12mm** - Medium labels
    - Font: 6pt body, 9pt title
    - Border: None
    - QR Code: Disabled by default
  - **30mm × 15mm** - Narrow labels
    - Font: 7pt body, 10pt title
    - Border: Simple
    - QR Code: Small, bottom-right position
  - **Default** - Fallback for unlisted sizes

## Configuration Interface

### Settings Page (Maintenance Module)

1. **Select Printer Type**
   - Choose from: 8 Labels, 14 Labels, Niimbot B1, Niimbot D110
   - This determines which label sizes are available

2. **Select Label Size** (for Niimbot printers only)
   - Dropdown shows sizes specific to the selected printer
   - Each size has independent settings
   - Sheet labels (8/14) don't show this option (static size)

3. **Configure Settings** (per label size)
   - **Font Size**: Body text size (6-12pt typically)
   - **Title Font Size**: Header text size (9-14pt typically)
   - **Border Style**: None, Simple, Double, Rounded
   - **Include QR Code**: Enable/disable QR code
   - **QR Size**: Small, Medium, Large
   - **QR Position**: Top-left, Top-right, Bottom-left, Bottom-right, Center-right
   - **QR Prefix**: URL prefix for QR codes (global setting)

4. **Live Preview**
   - Updates automatically as you adjust settings
   - Shows actual label appearance
   - Select preview printer type and size independently
   - Preview uses dummy data for visualization

## Database Storage

Settings are stored in the `SystemParameters` table with naming convention:
- **Default**: `label_<setting>` (e.g., `label_font_size`)
- **Per-size**: `label_<size>_<setting>` (e.g., `label_60x30mm_font_size`)
- **Global**: `label_qr_code_prefix` (shared across all sizes)

Example database keys:
```
label_60x30mm_font_size = 8
label_60x30mm_title_font_size = 12
label_60x30mm_border_style = simple
label_60x30mm_include_qr_code = true
label_60x30mm_qr_size = medium
label_60x30mm_qr_position = right
```

## Printing Labels

When printing a label:
1. Select printer type in the entry detail page
2. For Niimbot printers, the label size is detected automatically or can be specified
3. System retrieves size-specific settings from database
4. Falls back to default settings if size-specific settings not found
5. Generates label with appropriate layout and formatting
6. For thermal printers (B1/D110), inverts colors before printing

## Best Practices

### For B1 Printer (Larger Labels)
- Use 60mm × 30mm for detailed product information with QR codes
- Use 40mm × 24mm for standard product labels
- Use 30mm × 15mm for compact labels with minimal info
- Enable QR codes on larger labels, disable on smaller ones

### For D110 Printer (Narrower Labels)
- Use 75mm × 12mm for wide but thin labels (cable labels, shelf labels)
- Use 50mm × 14mm for general-purpose labels
- Typically disable QR codes due to limited height
- Use simpler borders or no borders for cleaner look

### For Sheet Labels (8/14)
- Fixed sizes, no configuration needed
- Best for bulk printing on standard printers
- 8-label sheets for larger items
- 14-label sheets for smaller items or mailing

## Troubleshooting

### Preview not updating
- Check browser console for JavaScript errors
- Ensure printer type is selected
- Verify label size is available for selected printer

### Settings not saving
- Check network tab for API errors
- Ensure values are within valid ranges
- Verify database permissions

### Wrong label size printing
- Confirm correct printer type selected
- Check that label size exists in printer's available sizes
- Verify physical label roll matches selected size

## Technical Details

### Label Size Calculations
Niimbot printers use 203 DPI:
- Formula: `pixels = mm × 203 / 25.4`
- Example: 60mm = 60 × 203 / 25.4 ≈ 480 pixels

### Color Inversion (Thermal Printers)
- B1 and D110 require inverted colors
- White prints as black on thermal paper
- System automatically inverts before sending to printer
- Uses `ImageOps.invert()` in Python

### Bluetooth Communication
- Uses BLE (Bluetooth Low Energy)
- B1 Protocol: 7-byte PrintStart, 6-byte SetPageSize
- D110 Protocol: Similar but with different width limits
- Automatic device discovery and connection

## Future Enhancements

Potential improvements:
- Custom label size input for unlisted sizes
- Template library for common label layouts
- Batch printing with different sizes
- Label design preview before printing
- Import/export label settings
