# Niimbot Label Printer Integration

## Overview

Added support for direct printing to Niimbot B1 and D110 Bluetooth label printers. This feature allows users to print labels directly from the application without needing to generate PDFs or use separate printer software.

## Features Implemented

### 1. **Two New Label Printer Options**
   - **Niimbot B1**: 384px width, supports larger labels
   - **Niimbot D110**: 240px width, compact label printer
   
### 2. **Bluetooth Printer Discovery**
   - Automatic discovery of nearby Niimbot printers
   - Shows printer name, address, and signal strength
   - Easy printer selection interface

### 3. **Direct Printing Capabilities**
   - Print directly to the selected Bluetooth printer
   - No intermediate PDFs or manual steps required
   - Support for multiple label sizes:
     - 30mm × 15mm
     - 40mm × 12mm
     - 50mm × 14mm (default)
     - 75mm × 12mm

### 4. **Customizable Print Settings**
   - **Density Control**: Adjustable from 1 (light) to 5 (dark)
   - **Quantity**: Print multiple copies (1-10)
   - **Label Size Selection**: Choose from common label sizes

### 5. **Label Preview**
   - Preview labels before printing
   - Optimized layout for small thermal labels
   - Includes QR codes and essential information

## Technical Implementation

### Backend Components

#### 1. **Niimbot Printer Service** (`app/services/niimbot_printer.py`)
   - Implements Niimbot protocol based on NiimPrintX specification
   - Uses `bleak` library for Bluetooth Low Energy communication
   - Handles:
     - Printer discovery
     - Connection management
     - Image encoding (monochrome conversion)
     - Print job execution

#### 2. **API Endpoints** (added to `app/api/labels_api.py`)
   - `GET /api/niimbot/discover` - Discover available printers
   - `POST /api/niimbot/connect` - Test printer connection
   - `POST /api/entries/<id>/niimbot/print` - Print label directly
   - `GET /api/niimbot/preview/<id>` - Preview label

#### 3. **Label Configuration**
   Updated `LABEL_CONFIGS` dictionary with Niimbot printer specifications:
   - Max width in pixels
   - DPI (203)
   - Common label sizes
   - Printer model information

### Frontend Components

#### 1. **Enhanced Label Selection Interface**
   When selecting a Niimbot printer type, the interface changes to show:
   - Label size dropdown
   - Density slider (1-5)
   - Quantity input
   - Printer discovery button
   - List of available printers
   - Selected printer information

#### 2. **Updated JavaScript** (`app/static/label_printing.js`)
   - Added Niimbot-specific UI functions
   - Integrated printer discovery
   - Direct print functionality
   - Preview support for Niimbot labels

## Dependencies

Added to `requirements.txt`:
```
bleak>=0.21.0       # Bluetooth Low Energy support (REQUIRED)
```

Note: `pycairo` is optional and not required for basic Niimbot functionality. It's only needed for advanced image processing features that we're not using. If you want to install it locally (not in Docker):
```bash
pip install pycairo>=1.20.0  # Optional, requires C compiler
```

## Installation Instructions

### 1. Install Dependencies
```bash
pip install bleak pycairo
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Enable Bluetooth
Ensure Bluetooth is enabled on your system:
- **Linux**: Bluetooth should be enabled and accessible
- **Windows**: Bluetooth adapter required
- **macOS**: Bluetooth should be enabled

### 3. Pair Your Niimbot Printer (Optional)
While not strictly necessary, pairing your printer with your system first can improve reliability:
1. Turn on your Niimbot printer
2. Put it in pairing mode (usually happens automatically when powered on)
3. Use your system's Bluetooth settings to discover and pair

## Usage Guide

### Printing a Label to Niimbot Printer

1. **Navigate to Entry Details**
   - Go to any entry in your application
   - Find the label printing section

2. **Select Printer Type**
   - Choose either "Niimbot B1" or "Niimbot D110" from the label type dropdown

3. **Configure Label Settings**
   - Select your label size (e.g., 50mm × 14mm)
   - Adjust print density (3 is recommended)
   - Set quantity if printing multiple copies

4. **Discover Your Printer**
   - Click "Discover Printers" button
   - Wait for the scan to complete (up to 10 seconds)
   - Select your printer from the list

5. **Preview (Optional)**
   - Click "Preview Label" to see how it will look
   - The preview shows the label optimized for the selected size

6. **Print**
   - Click "Print Label"
   - Wait for the print job to complete
   - Your label(s) will be printed directly to the Niimbot printer

## Label Design for Niimbot

Labels generated for Niimbot printers are optimized for thermal printing:

- **Monochrome**: Converted to black and white
- **Compact Layout**: Efficient use of limited space
- **Essential Information Only**:
  - Entry title (truncated if needed)
  - Entry type and ID
  - QR code (bottom right, smaller size)
  - Created date
- **No Logo**: Space constraints limit decorative elements
- **High DPI**: 203 DPI for crisp text on thermal labels

## Troubleshooting

### Printer Not Found
- Ensure printer is powered on and charged
- Check Bluetooth is enabled on your computer
- Move printer closer to computer
- Try turning printer off and on again

### Connection Failed
- Make sure no other device is connected to the printer
- Check printer battery level
- Restart Bluetooth on your computer

### Print Quality Issues
- Adjust density setting (try 4 or 5 for darker prints)
- Clean printer head if prints are faded
- Ensure you're using compatible label rolls

### Bluetooth Not Available Error
- Install bleak library: `pip install bleak`
- Check your system has Bluetooth hardware
- Ensure Bluetooth permissions are granted

## Supported Printer Models

Based on NiimPrintX specifications:
- ✅ **Niimbot B1** - Fully supported
- ✅ **Niimbot D110** - Fully supported
- 🔄 **Other models** (B18, B21, D11) - Can be added using same protocol

## Future Enhancements

Potential improvements:
1. Save printer selection for quick access
2. Batch printing from entry list
3. Template customization for Niimbot labels
4. Support for additional Niimbot models
5. Printer status monitoring (battery, paper)
6. Label design templates specific to different use cases

## Technical Notes

### Bluetooth Protocol
The implementation follows the Niimbot protocol discovered through reverse engineering:
- Uses BLE (Bluetooth Low Energy)
- Service UUIDs: `ae30` and `fff0` variants
- Characteristic UUIDs for read/write operations
- Custom packet format with checksums

### Image Encoding
Images are processed before sending:
1. Convert to grayscale
2. Apply threshold for monochrome conversion
3. Encode as binary bitmap
4. Split into line-by-line packets
5. Send with proper sequencing

### Print Flow
1. Set label density
2. Set label type
3. Start print job
4. Start page print
5. Set dimensions
6. Set quantity
7. Send image data (line by line)
8. End page print
9. Wait for completion
10. End print job

## Credits

Implementation based on the NiimPrintX project by Labbots:
- GitHub: https://github.com/Labbots/NiimPrintX
- Protocol documentation and reference implementation

## License

This feature integrates with the existing application license and uses the bleak library (MIT License).
