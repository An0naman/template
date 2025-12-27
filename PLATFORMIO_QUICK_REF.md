# PlatformIO Quick Reference

## 🚀 Quick Start Commands

### Build Commands
```bash
# Build for ESP32-WROOM-32
pio run -e esp32_wroom32

# Build for Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6

# Build all environments
pio run

# Clean build
pio run -t clean
```

### Upload Commands
```bash
# Upload to ESP32-WROOM-32
pio run -e esp32_wroom32 -t upload

# Upload to Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6 -t upload

# Upload and monitor
pio run -e esp32_wroom32 -t upload && pio device monitor
```

### Monitor
```bash
# Open serial monitor
pio device monitor

# Monitor with colors
pio device monitor --filter colorize
```

## 📋 Environment Names

| Command | Board | Notes |
|---------|-------|-------|
| `esp32_wroom32` | ESP32-WROOM-32 | Standard build |
| `esp32_wroom32_dev` | ESP32-WROOM-32 | Development mode |
| `esp32_wroom32_prod` | ESP32-WROOM-32 | Production mode |
| `firebeetle2_esp32c6` | Firebeetle 2 C6 | Standard build |
| `firebeetle2_esp32c6_dev` | Firebeetle 2 C6 | Development mode |
| `firebeetle2_esp32c6_prod` | Firebeetle 2 C6 | Production mode |

## 🔧 Common Tasks

### First Time Setup
```bash
# 1. Install PlatformIO
pip3 install platformio

# 2. Navigate to project
cd /home/an0naman/Documents/GitHub/template

# 3. Install dependencies
pio pkg install

# 4. Build to verify setup
pio run -e esp32_wroom32
```

### Development Workflow
```bash
# 1. Build
pio run -e esp32_wroom32

# 2. Upload
pio run -e esp32_wroom32 -t upload

# 3. Monitor
pio device monitor
```

### Switching Boards
```bash
# Test on ESP32-WROOM-32
pio run -e esp32_wroom32 -t upload
pio device monitor

# Ctrl+C to exit monitor

# Test on Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6 -t upload
pio device monitor
```

## 🎯 One-Liners

```bash
# Build, upload, and monitor in one command
pio run -e esp32_wroom32 -t upload && pio device monitor

# Clean and rebuild
pio run -e esp32_wroom32 -t clean && pio run -e esp32_wroom32

# List available serial ports
pio device list

# Install specific library
pio lib install "DallasTemperature"
```

## 📊 Comparison with Arduino IDE

| Task | Arduino IDE | PlatformIO |
|------|-------------|------------|
| Select board | Manual menu | `pio run -e esp32_wroom32` |
| Upload | Click button | `pio run -e esp32_wroom32 -t upload` |
| Monitor | Open Serial | `pio device monitor` |
| Libraries | Library Manager | Auto-installed from platformio.ini |
| Multi-board | Change board each time | `pio run` (builds all) |

## 🐛 Troubleshooting

### Issue: Command not found
```bash
# Add to PATH (Linux/Mac)
export PATH=$PATH:~/.local/bin

# Or use full path
~/.local/bin/pio run -e esp32_wroom32
```

### Issue: Port permission denied
```bash
# Linux: Add user to dialout group
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Issue: Library not found
```bash
# Install all dependencies
pio pkg install

# Or install specific library
pio lib install "ArduinoJson@^7.0.0"
```

## ✨ Benefits for Multi-Board

### Arduino IDE Workflow:
```
1. Open .ino file
2. Tools → Board → ESP32 Dev Module
3. Upload
4. [Want to test C6]
5. Tools → Board → Firebeetle 2 ESP32-C6
6. Tools → USB CDC On Boot → Enabled
7. Upload
```

### PlatformIO Workflow:
```bash
# ESP32-WROOM-32
pio run -e esp32_wroom32 -t upload

# Firebeetle 2 ESP32-C6
pio run -e firebeetle2_esp32c6 -t upload

# That's it! All settings in platformio.ini
```

## 🎓 Pro Tips

1. **Use VS Code Extension**: More GUI-friendly
2. **Enable Auto-upload**: Builds and uploads on save
3. **Use OTA environments**: Update devices wirelessly
4. **CI/CD Ready**: Easy to integrate with GitHub Actions
5. **Build all boards**: `pio run` builds all environments

## 📚 Further Reading

- Full guide: `PLATFORMIO_GUIDE.md`
- Board support: `BOARD_SUPPORT.md`
- Testing: `TESTING_MULTI_BOARD.md`
