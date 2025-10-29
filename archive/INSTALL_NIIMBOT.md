# Quick Installation Guide: Niimbot Printer Support

## Prerequisites

- Python 3.7+
- Bluetooth adapter (built-in or USB)
- Niimbot B1 or D110 printer

## Installation Steps

### 1. Install Python Dependencies

```bash
# Install required Bluetooth library
pip install bleak>=0.21.0
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

**Note**: `pycairo` is optional and not required for Niimbot printing. If you need it for other features:

```bash
# Optional - only if needed for advanced features
pip install pycairo>=1.20.0
```

### 2. System-Specific Setup

#### Linux (Ubuntu/Debian)
```bash
# Install Bluetooth libraries
sudo apt-get update
sudo apt-get install bluetooth bluez libbluetooth-dev

# Ensure Bluetooth service is running
sudo systemctl start bluetooth
sudo systemctl enable bluetooth

# Add user to bluetooth group (optional)
sudo usermod -a -G bluetooth $USER
```

#### macOS
```bash
# Bluetooth is built-in, just ensure it's enabled
# Install cairo if needed
brew install cairo pkg-config
```

#### Windows
```bash
# Ensure Bluetooth is enabled in Windows settings
# No additional system packages needed
```

### 3. Verify Installation

Run this Python script to test:

```python
import asyncio

async def test_bluetooth():
    try:
        from bleak import BleakScanner
        print("✓ Bleak library imported successfully")
        
        print("Scanning for Bluetooth devices...")
        devices = await BleakScanner.discover(timeout=5.0)
        print(f"✓ Found {len(devices)} Bluetooth device(s)")
        
        return True
    except ImportError:
        print("✗ Bleak library not installed")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bluetooth())
```

### 4. Test Printer Discovery

Start your Flask application and navigate to any entry's label printing page:

1. Select "Niimbot B1" or "Niimbot D110" from the label type dropdown
2. Click "Discover Printers"
3. Your printer should appear in the list (make sure it's turned on!)

## Troubleshooting

### "Bluetooth support not available" Error

**Solution**: Install bleak library
```bash
pip install bleak
```

### Permission Denied on Linux

**Solution**: Add user to bluetooth group
```bash
sudo usermod -a -G bluetooth $USER
# Log out and log back in
```

### Printer Not Discovered

1. **Check printer is on**: LED should be lit
2. **Check battery**: Low battery can cause connection issues
3. **Reset printer**: Turn off and on again
4. **Check distance**: Keep printer within 10 meters
5. **Check pairing**: Some systems require initial pairing

### Import Error: pycairo

If you get pycairo errors:

**Linux**:
```bash
sudo apt-get install libcairo2-dev pkg-config python3-dev
pip install pycairo
```

**macOS**:
```bash
brew install cairo pkg-config
pip install pycairo
```

**Windows**:
```bash
# Download and install from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pycairo
# Or use conda:
conda install -c conda-forge pycairo
```

## First Print Test

1. **Power on your Niimbot printer**
2. **Open any entry in your application**
3. **Select printer type** (B1 or D110)
4. **Choose label size** (try 50mm × 14mm)
5. **Click "Discover Printers"**
6. **Select your printer from the list**
7. **Click "Preview Label"** to see what it will look like
8. **Click "Print Label"**

Success! You should now have a printed label.

## Need Help?

See the full documentation in `NIIMBOT_PRINTER_INTEGRATION.md`
