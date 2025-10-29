# Niimbot Printer Integration

Complete guide to setting up and using Niimbot B1 and D110 Bluetooth thermal printers.

## Overview

Niimbot printers are compact thermal label printers that connect via Bluetooth. No ink or toner required - labels are printed using heat-sensitive paper.

**Supported Models**:
- **B1** - 48mm max width (203 DPI)
- **D110** - 72mm max width (203 DPI)

---

## Quick Start

### 1. Pair Printer (One-Time Setup)

```bash
# Open Bluetooth controller
bluetoothctl

# Scan for devices
scan on

# Wait for "B1_XXXX" or "D110_XXXX" to appear
# Note the MAC address (XX:XX:XX:XX:XX:XX)

# Pair the device
pair XX:XX:XX:XX:XX:XX

# Trust the device (auto-connect)
trust XX:XX:XX:XX:XX:XX

# Exit
exit
```

### 2. Run Application with Bluetooth

```bash
# Docker has limited Bluetooth support - run natively
docker compose down
./run_with_bluetooth.sh
```

Access at: `http://localhost:5001`

### 3. Print a Label

1. Navigate to any entry's details page
2. Select "Niimbot B1" or "Niimbot D110" from dropdown
3. Choose label size (e.g., 60mm × 30mm)
4. Click "Discover Printers"
5. Select your printer from the list
6. Click "Print Label"

---

## Supported Label Sizes

### Niimbot B1 (48mm max width)

| Size | Use Case | QR Code | Border |
|------|----------|---------|--------|
| 60×30mm | Large product labels | Medium | Simple |
| 40×24mm | Medium labels | Medium | Simple |
| 40×20mm | Standard labels | Small | Simple |
| 30×15mm | Small labels | Small | Simple |
| 30×12mm | Tiny labels | None | None |

### Niimbot D110 (72mm max width)

| Size | Use Case | QR Code | Border |
|------|----------|---------|--------|
| 75×12mm | Wide cable/shelf labels | Small | None |

### Custom Sizes

Add custom sizes via database:
```sql
INSERT INTO SystemParameters (parameter_name, parameter_value)
VALUES 
  ('label_50x25mm_font_size', '8'),
  ('label_50x25mm_title_font_size', '11'),
  ('label_50x25mm_border_style', 'simple');
```

---

## Installation & Setup

### System Requirements

**Linux (Recommended)**:
- BlueZ 5.50+
- Python 3.12+
- `bleak` package (installed via requirements.txt)

**Docker Limitations**:
- Docker has poor Bluetooth support
- Must run natively for Bluetooth printers
- USB Bluetooth adapters may not work in containers

### Install Dependencies

```bash
# Update package list
sudo apt update

# Install Bluetooth tools
sudo apt install -y bluez bluetooth libbluetooth-dev

# Verify Bluetooth service
sudo systemctl status bluetooth

# Enable if not running
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### Application Setup

```bash
# Clone and enter directory
cd /path/to/template

# Install Python dependencies
pip install -r requirements.txt

# Make run script executable
chmod +x run_with_bluetooth.sh

# Run with Bluetooth support
./run_with_bluetooth.sh
```

### Verify Bluetooth

```bash
# Check Bluetooth adapter
bluetoothctl show

# Should show:
# Powered: yes
# Discoverable: yes (optional)
# Pairable: yes
```

---

## Pairing Process

### Method 1: BluetoothCTL (Recommended)

```bash
bluetoothctl

# Enable agent
agent on
default-agent

# Scan for devices
scan on

# Wait for printer to appear:
# [NEW] Device XX:XX:XX:XX:XX:XX B1_XXXX
# Note the MAC address

# Pair
pair XX:XX:XX:XX:XX:XX

# Trust (auto-reconnect)
trust XX:XX:XX:XX:XX:XX

# Connect (optional - app does this)
connect XX:XX:XX:XX:XX:XX

# Exit
quit
```

### Method 2: Auto-Discovery Script

```bash
# Use included pairing script
./pair_niimbot.sh

# Follow prompts
# Script will:
# 1. Scan for Niimbot devices
# 2. Show available printers
# 3. Pair and trust selected device
```

### Method 3: GUI (Desktop Linux)

1. Open Bluetooth settings
2. Make printer discoverable (blue light blinking)
3. Click "Add Device"
4. Select "B1_XXXX" or "D110_XXXX"
5. Click "Pair"
6. Trust device for auto-connect

---

## Printing

### Via Web Interface

1. **Select Printer**:
   - Go to entry details page
   - Choose "Niimbot B1" or "Niimbot D110" from dropdown

2. **Configure Label**:
   - Select size (60×30mm, 40×20mm, etc.)
   - Set print density (1-5, recommend 3)
   - Choose quantity (1-10 copies)

3. **Discover Printer**:
   - Click "Discover Printers" button
   - Wait 5-10 seconds for scan
   - Select your printer from list

4. **Print**:
   - Click "Preview Label" (optional - see before printing)
   - Click "Print Label"
   - Label should print immediately

### Via API

```python
import requests

# Print label
response = requests.post('http://localhost:5001/api/labels/print_niimbot', json={
    'entry_id': 42,
    'printer_address': 'XX:XX:XX:XX:XX:XX',
    'label_size': '60x30mm',
    'density': 3,
    'quantity': 2,
    'printer_type': 'b1'
})

print(response.json())
# {'success': True, 'message': 'Printed 2 labels successfully'}
```

### Via Command Line

```bash
# Discover printers
curl http://localhost:5001/api/labels/discover_printers?printer_type=b1

# Print label
curl -X POST http://localhost:5001/api/labels/print_niimbot \
  -H "Content-Type: application/json" \
  -d '{
    "entry_id": 42,
    "printer_address": "XX:XX:XX:XX:XX:XX",
    "label_size": "60x30mm",
    "density": 3,
    "quantity": 1,
    "printer_type": "b1"
  }'
```

---

## Troubleshooting

### Printer Not Discovered

**Symptoms**: "No printers found" message

**Solutions**:
1. **Check printer is on**:
   - Blue light should be blinking (pairing mode)
   - Press power button for 3 seconds if off

2. **Verify Bluetooth enabled**:
   ```bash
   bluetoothctl show
   # Should show: Powered: yes
   
   # If not, enable:
   bluetoothctl power on
   ```

3. **Check pairing**:
   ```bash
   bluetoothctl devices
   # Should list: Device XX:XX:XX:XX:XX:XX B1_XXXX
   
   # If not paired:
   bluetoothctl pair XX:XX:XX:XX:XX:XX
   bluetoothctl trust XX:XX:XX:XX:XX:XX
   ```

4. **Remove and re-pair**:
   ```bash
   bluetoothctl remove XX:XX:XX:XX:XX:XX
   # Then pair again
   ```

5. **Restart Bluetooth service**:
   ```bash
   sudo systemctl restart bluetooth
   ```

### Connection Fails

**Symptoms**: "Failed to connect to printer"

**Solutions**:
1. **Check printer not paired with other device**:
   - Disconnect from phone/computer
   - Only one connection at a time

2. **Verify MAC address correct**:
   ```bash
   bluetoothctl devices
   # Double-check address matches
   ```

3. **Test connection manually**:
   ```bash
   bluetoothctl connect XX:XX:XX:XX:XX:XX
   # Should show: Connection successful
   ```

4. **Check application has Bluetooth permissions**:
   ```bash
   # Run as user (not root)
   ./run_with_bluetooth.sh
   ```

### Print Quality Issues

**Symptoms**: Faded, unclear, or blank labels

**Solutions**:
1. **Adjust print density**:
   - Try values 2-4
   - 3 is usually optimal
   - Higher = darker (but slower)

2. **Check label type**:
   - Must use thermal paper
   - Labels have heat-sensitive coating
   - Standard paper won't work

3. **Clean printhead**:
   - Turn off printer
   - Use isopropyl alcohol on cotton swab
   - Gently clean printhead
   - Let dry completely

4. **Check label alignment**:
   - Labels must feed straight
   - Adjust guide rails
   - Remove jams/wrinkles

5. **Printer temperature**:
   - Let printer cool if hot
   - Overheating reduces quality

### "Printer Busy" Error

**Symptoms**: Print job rejected, printer shows busy

**Solutions**:
1. **Wait and retry**:
   - Printer may be processing
   - Wait 10-15 seconds
   - Try again

2. **Power cycle printer**:
   - Turn off
   - Wait 5 seconds
   - Turn on
   - Reconnect

3. **Cancel pending jobs**:
   - Some printers queue jobs
   - Power cycle clears queue

### Docker Bluetooth Issues

**Symptoms**: Bluetooth not working in Docker

**Why**: Docker containers have limited hardware access

**Solutions**:
1. **Run natively** (recommended):
   ```bash
   docker compose down
   ./run_with_bluetooth.sh
   ```

2. **Use privileged mode** (security risk):
   ```yaml
   # docker-compose.yml
   services:
     app:
       privileged: true
       network_mode: host
       volumes:
         - /var/run/dbus:/var/run/dbus
         - /run/dbus:/run/dbus
   ```

3. **USB Bluetooth adapter**:
   - Pass through USB device
   - May not work with all adapters

### Permission Denied Errors

**Symptoms**: "Permission denied" when accessing Bluetooth

**Solutions**:
1. **Add user to bluetooth group**:
   ```bash
   sudo usermod -a -G bluetooth $USER
   # Log out and back in
   ```

2. **Check D-Bus permissions**:
   ```bash
   ls -l /var/run/dbus/system_bus_socket
   # Should be readable by user
   ```

3. **Run with correct user**:
   ```bash
   # Don't use sudo
   ./run_with_bluetooth.sh
   ```

---

## Advanced Configuration

### Custom Label Sizes

Add to `SystemParameters` table:

```sql
-- 50mm × 25mm custom size
INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES
  ('label_50x25mm_font_size', '8'),
  ('label_50x25mm_title_font_size', '11'),
  ('label_50x25mm_border_style', 'simple'),
  ('label_50x25mm_include_qr_code', 'true'),
  ('label_50x25mm_qr_size', 'medium'),
  ('label_50x25mm_qr_position', 'right');
```

Update dropdown in `templates/entry_details.html`:
```html
<option value="50x25mm">50mm × 25mm</option>
```

### Print Density Optimization

Different label types need different densities:

| Label Type | Recommended Density |
|------------|-------------------|
| White matte | 3 |
| White glossy | 2-3 |
| Transparent | 4-5 |
| Colored | 3-4 |

Test with sample before bulk printing.

### Batch Printing

Print multiple labels efficiently:

```python
# API batch print
for entry_id in [1, 2, 3, 4, 5]:
    requests.post('http://localhost:5001/api/labels/print_niimbot', json={
        'entry_id': entry_id,
        'printer_address': 'XX:XX:XX:XX:XX:XX',
        'label_size': '60x30mm',
        'density': 3,
        'quantity': 1,
        'printer_type': 'b1'
    })
    time.sleep(2)  # Wait between prints
```

### Multiple Printers

Connect multiple printers:

```bash
# Pair both printers
bluetoothctl pair XX:XX:XX:XX:XX:01  # Printer 1
bluetoothctl pair XX:XX:XX:XX:XX:02  # Printer 2

# Discovery shows both
# Select desired printer from dropdown
```

---

## Hardware Specifications

### Niimbot B1

- **Print Method**: Direct thermal
- **Print Speed**: 18mm/s
- **Resolution**: 203 DPI
- **Max Width**: 48mm (384px)
- **Connectivity**: Bluetooth 4.0 BLE
- **Battery**: 1500mAh rechargeable
- **Charge Time**: 2-3 hours
- **Labels per Charge**: ~300 (40×20mm)
- **Dimensions**: 110 × 85 × 60mm
- **Weight**: 260g

### Niimbot D110

- **Print Method**: Direct thermal
- **Print Speed**: 20mm/s
- **Resolution**: 203 DPI
- **Max Width**: 72mm (576px)
- **Connectivity**: Bluetooth 4.0 BLE
- **Power**: USB-C (no battery)
- **Dimensions**: 135 × 95 × 70mm
- **Weight**: 320g

---

## Label Types & Paper

### Compatible Label Rolls

**B1 Printers**:
- 30mm width rolls
- 40mm width rolls
- Core: 25mm inner diameter
- Roll diameter: Up to 80mm

**D110 Printers**:
- 50mm width rolls
- 75mm width rolls
- Core: 25mm inner diameter
- Roll diameter: Up to 100mm

### Paper Types

- **Thermal Paper**: Standard (most common)
- **Thermal Transfer**: Requires ribbon (not supported)
- **Waterproof**: Synthetic thermal (more durable)
- **Colored**: Pre-colored thermal paper

### Where to Buy

- **Official Niimbot Store**: Amazon, AliExpress
- **Generic Thermal Labels**: Compatible, cheaper
- **Size**: Match your printer's max width
- **Quality**: Look for long-lasting thermal coating

---

## Related Documentation

- [Label Printing Guide](./LABEL_PRINTING.md) - All label types
- [Installation Guide](../setup/INSTALLATION.md) - System setup
- [Bluetooth Setup Guide](../setup/BLUETOOTH.md) - Detailed Bluetooth config

---

## Changelog

**v1.0** - Initial B1 support
**v1.1** - Added D110 support
**v1.2** - Auto-discovery feature
**v1.3** - Multiple printer support
**v1.4** - Improved error handling
