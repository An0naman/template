# PlatformIO Multi-Board Setup Guide

## 🚀 Why PlatformIO?

PlatformIO is **superior** to Arduino IDE for multi-board development:
- ✅ Better dependency management
- ✅ Built-in board configurations
- ✅ Multiple environments in one project
- ✅ Command-line interface for automation
- ✅ VS Code integration
- ✅ Better build system
- ✅ Library management
- ✅ Over-the-Air (OTA) updates built-in

## 📁 Project Structure

```
template/
├── platformio.ini          # Board configurations
├── src/
│   └── main.cpp           # Main firmware (was sensor_firmware.ino)
├── include/
│   └── esp32_web_interface.h
├── lib/                   # Custom libraries (if needed)
└── test/                  # Unit tests (optional)
```

## 🔧 Installation

### Option 1: VS Code Extension (Recommended)
1. Install VS Code
2. Install "PlatformIO IDE" extension
3. Restart VS Code
4. Open project folder

### Option 2: Command Line
```bash
# Install Python 3.6+
sudo apt-get install python3 python3-pip

# Install PlatformIO Core
pip3 install platformio

# Verify installation
pio --version
```

## 📋 Available Environments

| Environment | Board | Usage |
|------------|-------|-------|
| `esp32_wroom32` | ESP32-WROOM-32 | Default development |
| `esp32_wroom32_dev` | ESP32-WROOM-32 | Development (debug) |
| `esp32_wroom32_prod` | ESP32-WROOM-32 | Production (optimized) |
| `firebeetle2_esp32c6` | Firebeetle 2 ESP32-C6 | C6 development |
| `firebeetle2_esp32c6_dev` | Firebeetle 2 ESP32-C6 | C6 dev (debug) |
| `firebeetle2_esp32c6_prod` | Firebeetle 2 ESP32-C6 | C6 prod (optimized) |
| `esp32_wroom32_ota` | ESP32-WROOM-32 | Over-the-air updates |
| `firebeetle2_esp32c6_ota` | Firebeetle 2 ESP32-C6 | OTA for C6 |

## 🎯 Quick Start

### Using VS Code PlatformIO Extension

1. **Open Project:**
   - File → Open Folder → Select `template/`
   - PlatformIO will auto-detect `platformio.ini`

2. **Select Environment:**
   - Click PlatformIO icon in sidebar
   - Expand environment (e.g., `env:esp32_wroom32`)

3. **Build:**
   - Click "Build" button
   - Or: `Ctrl+Alt+B`

4. **Upload:**
   - Connect board via USB
   - Click "Upload" button
   - Or: `Ctrl+Alt+U`

5. **Monitor:**
   - Click "Serial Monitor"
   - Or: `Ctrl+Alt+S`

### Using Command Line

```bash
# Navigate to project
cd /home/an0naman/Documents/GitHub/template

# List available environments
pio run --list-targets

# Build for ESP32-WROOM-32
pio run -e esp32_wroom32

# Build for Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6

# Upload to ESP32-WROOM-32
pio run -e esp32_wroom32 -t upload

# Upload to Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6 -t upload

# Monitor serial output
pio device monitor

# Build and upload in one command
pio run -e esp32_wroom32 -t upload && pio device monitor
```

## 🔨 Common Commands

### Building

```bash
# Build default environment
pio run

# Build specific environment
pio run -e esp32_wroom32
pio run -e firebeetle2_esp32c6

# Build all environments
pio run

# Clean build
pio run -t clean

# Build with verbose output
pio run -v
```

### Uploading

```bash
# Upload to specific port
pio run -e esp32_wroom32 -t upload --upload-port /dev/ttyUSB0

# Auto-detect port and upload
pio run -e esp32_wroom32 -t upload

# Upload via OTA (Over-the-Air)
pio run -e esp32_wroom32_ota -t upload
```

### Monitoring

```bash
# Start serial monitor
pio device monitor

# Monitor with specific baud rate
pio device monitor -b 115200

# Monitor with filters (colors, timestamps)
pio device monitor --filter colorize --filter time
```

### Library Management

```bash
# Search for library
pio lib search "DallasTemperature"

# Install library
pio lib install "DallasTemperature"

# List installed libraries
pio lib list

# Update all libraries
pio lib update
```

## 🎛️ Environment-Specific Builds

### Development Build (with debug symbols)
```bash
pio run -e esp32_wroom32_dev -t upload
```
- Debug symbols enabled
- `DEBUG_MODE=1`
- `IS_PRODUCTION=false`
- Development server (port 5001)

### Production Build (optimized)
```bash
pio run -e esp32_wroom32_prod -t upload
```
- Optimized for size/speed
- `DEBUG_MODE=0`
- `IS_PRODUCTION=true`
- Production server (port 5005)

## 🌐 Over-the-Air (OTA) Updates

### Setup

1. **First, upload via USB** to enable OTA:
   ```bash
   pio run -e esp32_wroom32 -t upload
   ```

2. **Find device IP address:**
   - Check serial monitor output
   - Or check your router's DHCP leases

3. **Update `platformio.ini` OTA settings:**
   ```ini
   [env:esp32_wroom32_ota]
   upload_port = 192.168.1.100  ; Your ESP32's IP
   ```

4. **Upload via OTA:**
   ```bash
   pio run -e esp32_wroom32_ota -t upload
   ```

### OTA Benefits
- No USB cable needed
- Update devices remotely
- Faster upload (network speed)
- Can update devices in hard-to-reach places

## 🔄 Switching Between Boards

### Scenario 1: Testing on Different Hardware

```bash
# Build for ESP32-WROOM-32
pio run -e esp32_wroom32

# Now switch to Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6

# Both use same source code!
# PlatformIO handles board-specific configs
```

### Scenario 2: Production Deployment

```bash
# Test on development board first
pio run -e esp32_wroom32_dev -t upload
# Test features, check serial output

# Deploy to production
pio run -e esp32_wroom32_prod -t upload
```

## 🐛 Troubleshooting

### Issue: Port not found
```bash
# List available ports
pio device list

# Specify port manually
pio run -t upload --upload-port /dev/ttyUSB0  # Linux
pio run -t upload --upload-port COM3         # Windows
```

### Issue: ESP32-C6 not recognized
```bash
# Update PlatformIO platform
pio pkg update

# Check platform version (need 6.5.0+ for C6)
pio platform show espressif32
```

### Issue: Library not found
```bash
# Install missing libraries
pio lib install

# Or install specific library
pio lib install "ArduinoJson@^7.0.0"
```

### Issue: Permission denied (Linux)
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again
# Or reboot
```

## 📊 Build Comparison

### Arduino IDE vs PlatformIO

| Feature | Arduino IDE | PlatformIO |
|---------|-------------|------------|
| Multi-board | Manual switching | One command |
| Libraries | Manual install | Auto-install |
| Build speed | Slow | Fast (caching) |
| CI/CD | Difficult | Easy |
| Debugging | Limited | Full GDB |
| OTA | Manual setup | Built-in |
| Code navigation | Basic | Advanced |

## 🎓 Advanced Usage

### Continuous Integration

```yaml
# .github/workflows/build.yml
name: PlatformIO CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install PlatformIO
      run: pip install platformio
    - name: Build ESP32-WROOM-32
      run: pio run -e esp32_wroom32
    - name: Build Firebeetle 2 ESP32-C6
      run: pio run -e firebeetle2_esp32c6
```

### Custom Build Script

```bash
#!/bin/bash
# build_all.sh

echo "Building all board variants..."

boards=("esp32_wroom32" "firebeetle2_esp32c6")

for board in "${boards[@]}"; do
    echo "Building $board..."
    pio run -e $board
    if [ $? -eq 0 ]; then
        echo "✅ $board build successful"
    else
        echo "❌ $board build failed"
        exit 1
    fi
done

echo "✅ All builds successful!"
```

### Testing

```bash
# Run unit tests
pio test -e esp32_wroom32

# Run specific test
pio test -e esp32_wroom32 -f test_sensors
```

## 🔍 Verification

After setting up PlatformIO, verify everything works:

```bash
# 1. Check PlatformIO version
pio --version

# 2. Check project is valid
pio project config

# 3. List available environments
pio project config --list-targets

# 4. Test build (don't upload)
pio run -e esp32_wroom32

# 5. Check build output
ls -lh .pio/build/esp32_wroom32/firmware.bin
```

Expected output:
```
✅ PlatformIO version: 6.x.x
✅ Project: template
✅ Environments: esp32_wroom32, firebeetle2_esp32c6, ...
✅ Build successful
✅ firmware.bin created (~800KB)
```

## 📚 Resources

- [PlatformIO Documentation](https://docs.platformio.org/)
- [ESP32 Platform Docs](https://docs.platformio.org/en/latest/platforms/espressif32.html)
- [PlatformIO CLI Reference](https://docs.platformio.org/en/latest/core/userguide/index.html)
- [VS Code PlatformIO IDE](https://docs.platformio.org/en/latest/integration/ide/vscode.html)

## 🎉 Benefits for This Project

1. **Single Command Deploy:**
   ```bash
   pio run -e esp32_wroom32 -t upload        # Upload to WROOM-32
   pio run -e firebeetle2_esp32c6 -t upload  # Upload to C6
   ```

2. **Automatic Board Detection:**
   - No manual defines needed
   - PlatformIO sets `CONFIG_IDF_TARGET_ESP32` or `CONFIG_IDF_TARGET_ESP32C6`
   - Firmware automatically configures correct pins

3. **Better Development Workflow:**
   - Build both variants in CI/CD
   - Test on one board, deploy to another
   - OTA updates to deployed devices

4. **Library Management:**
   - All dependencies in `platformio.ini`
   - Automatic installation
   - Version locking

## ✅ Next Steps

1. **Install PlatformIO** (VS Code extension or CLI)
2. **Open project** in VS Code
3. **Build** both environments:
   ```bash
   pio run -e esp32_wroom32
   pio run -e firebeetle2_esp32c6
   ```
4. **Upload** to your board:
   ```bash
   pio run -e esp32_wroom32 -t upload
   ```
5. **Monitor** serial output:
   ```bash
   pio device monitor
   ```

**That's it!** PlatformIO handles all the board-specific configuration automatically. 🚀
