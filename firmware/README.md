# Firmware Directory

This directory contains firmware for various IoT devices supported by this project.

## Available Firmware

### FireBeetle 2 ESP32-C6
**Path**: [`firebeetle_esp32c6/`](firebeetle_esp32c6/)

Production-ready firmware for the DFRobot FireBeetle 2 ESP32-C6 board with:
- ✅ Calibrated battery monitoring (GPIO 0)
- ✅ Dynamic logic system with JSON configuration
- ✅ Built-in web interface for configuration
- ✅ OTA firmware updates
- ✅ Multi-sensor support (DHT22, analog, digital, I2C)
- ✅ RESTful API endpoints

**Quick Start**: [firebeetle_esp32c6/QUICKSTART.md](firebeetle_esp32c6/QUICKSTART.md)  
**Documentation**: [firebeetle_esp32c6/README.md](firebeetle_esp32c6/README.md)  
**Examples**: [firebeetle_esp32c6/LOGIC_EXAMPLES.md](firebeetle_esp32c6/LOGIC_EXAMPLES.md)

---

## Building Firmware

All firmware uses PlatformIO for building and flashing.

### Prerequisites
```bash
# Install PlatformIO
pip install platformio

# Or use the PlatformIO IDE extension for VS Code
```

### General Workflow
```bash
# Navigate to specific firmware directory
cd firmware/firebeetle_esp32c6

# Build
pio run

# Upload to device
pio run -t upload

# Monitor serial output
pio device monitor
```

---

## Directory Structure

```
firmware/
├── README.md                      # This file
└── firebeetle_esp32c6/           # FireBeetle 2 ESP32-C6 firmware
    ├── README.md                  # Complete documentation
    ├── QUICKSTART.md              # 5-minute setup guide
    ├── LOGIC_EXAMPLES.md          # Ready-to-use configurations
    ├── sensor_firmware.ino        # Main firmware code
    ├── esp32_web_interface.h      # Web UI
    └── platformio.ini             # Build configuration
```

---

## Adding New Firmware

When adding firmware for a new board:

1. Create a new directory: `firmware/board_name/`
2. Include these files:
   - `README.md` - Complete documentation
   - `QUICKSTART.md` - Quick setup guide
   - Main firmware files
   - `platformio.ini` or equivalent build config
3. Update this file to list the new firmware
4. Add examples if applicable

---

## Hardware Compatibility

| Board | Firmware | Status | Notes |
|-------|----------|--------|-------|
| FireBeetle 2 ESP32-C6 | `firebeetle_esp32c6/` | ✅ Production | Calibrated battery monitoring |
| Generic ESP32 | `firebeetle_esp32c6/` | ⚠️ Compatible | Use esp32_wroom32 build env, no battery monitoring |

---

## Support

For firmware issues:
1. Check the board-specific README
2. Review the QUICKSTART guide
3. Check serial monitor output
4. Search issues on GitHub
5. Create new issue with logs

---

**Last Updated**: December 29, 2025
