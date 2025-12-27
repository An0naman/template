# ESP32 Board Support Documentation

## Overview

The sensor firmware now supports multiple ESP32 board types with automatic detection and board-specific pin configurations.

## Supported Boards

### 1. ESP32-WROOM-32 (Original ESP32)
- **Board Type ID**: `esp32_wroom32`
- **Chip**: ESP32 (Xtensa dual-core)
- **Detection**: Automatically detected via `CONFIG_IDF_TARGET_ESP32`

**Pin Configuration:**
- Temperature Sensor (OneWire): GPIO4
- Relay Control: GPIO25
- Status LED: GPIO2 (built-in)
- Battery Voltage Reading: GPIO34 (ADC1_CH6)

**Arduino IDE Setup:**
1. Board: "ESP32 Dev Module"
2. Flash Size: 4MB
3. Partition Scheme: Default
4. Upload Speed: 921600

---

### 2. Firebeetle 2 ESP32-C6
- **Board Type ID**: `firebeetle2_esp32c6`
- **Chip**: ESP32-C6 (RISC-V single-core)
- **Detection**: Automatically detected via `CONFIG_IDF_TARGET_ESP32C6`

**Pin Configuration:**
- Temperature Sensor (OneWire): GPIO15
- Relay Control: GPIO14
- Status LED: GPIO15 (RGB LED, shared)
- Battery Voltage Reading: GPIO2

**Arduino IDE Setup:**
1. Board: "DFRobot Firebeetle 2 ESP32-C6" or "ESP32C6 Dev Module"
2. Flash Size: 4MB
3. Partition Scheme: Default
4. USB CDC On Boot: Enabled
5. Upload Speed: 921600

**Special Notes for ESP32-C6:**
- Uses RISC-V architecture (not Xtensa)
- Single core processor
- Lower power consumption
- USB-C native support
- Integrated battery charging circuit
- RGB LED on GPIO15

---

## Firmware Features

### Automatic Board Detection

The firmware automatically detects the board type at compile time using preprocessor directives:

```cpp
#if CONFIG_IDF_TARGET_ESP32C6
    #define BOARD_TYPE "firebeetle2_esp32c6"
    // ESP32-C6 specific pins
#elif CONFIG_IDF_TARGET_ESP32
    #define BOARD_TYPE "esp32_wroom32"
    // ESP32-WROOM-32 specific pins
#endif
```

### Registration with Master Control

When registering with the Sensor Master Control system, the firmware sends:
- `sensor_type`: Board type ID (e.g., "esp32_wroom32" or "firebeetle2_esp32c6")
- `board_type`: Explicit board type identifier
- `hardware_info`: Human-readable board name and chip model

Example registration payload:
```json
{
  "sensor_id": "esp32_fermentation_mk2",
  "sensor_name": "Fermentation Chamber",
  "sensor_type": "firebeetle2_esp32c6",
  "board_type": "firebeetle2_esp32c6",
  "hardware_info": "Firebeetle 2 ESP32-C6 (ESP32-C6)",
  "firmware_version": "2.1.0",
  "capabilities": ["temperature", "relay_control", "analog_read", "read_battery"]
}
```

---

## Compiling for Different Boards

### Using Arduino IDE

1. **For ESP32-WROOM-32:**
   - Tools → Board → ESP32 Arduino → "ESP32 Dev Module"
   - Upload normally

2. **For Firebeetle 2 ESP32-C6:**
   - Install ESP32 board support (version 3.0.0 or higher required for C6)
   - Tools → Board → ESP32 Arduino → "DFRobot Firebeetle 2 ESP32-C6"
   - Tools → USB CDC On Boot → "Enabled"
   - Upload normally

### Using PlatformIO

Create separate environments in `platformio.ini`:

```ini
[env:esp32_wroom32]
platform = espressif32
board = esp32dev
framework = arduino

[env:firebeetle2_esp32c6]
platform = espressif32
board = dfrobot_firebeetle2_esp32c6
framework = arduino
build_flags = 
    -DCONFIG_IDF_TARGET_ESP32C6
```

---

## Pin Mapping Reference

| Function | ESP32-WROOM-32 | Firebeetle 2 C6 | Notes |
|----------|----------------|-----------------|-------|
| Temperature Sensor | GPIO4 | GPIO15 | OneWire/Dallas |
| Relay Control | GPIO25 | GPIO14 | Digital Output |
| Status LED | GPIO2 | GPIO15 | Built-in LED |
| Battery Voltage | GPIO34 | GPIO2 | ADC Input |

---

## Sensor Master Control Integration

The Sensor Master Control system now tracks board types:

1. **Database**: `SensorRegistration` table includes `board_type` column
2. **API**: Registration endpoint accepts `board_type` field
3. **UI**: Dashboard displays board type badge for each sensor

### Viewing Board Type in Dashboard

Navigate to **Sensor Master Control** page to see:
- Sensor ID
- Sensor Name
- **Board Type** badge (shows "ESP32-WROOM-32" or "Firebeetle 2 ESP32-C6")
- Status
- Last Check-in

---

## Troubleshooting

### ESP32-C6 Not Detected

**Problem**: Firmware compiles for ESP32 instead of ESP32-C6

**Solutions**:
1. Ensure you have ESP32 Arduino Core 3.0.0 or higher
2. Select the correct board in Arduino IDE
3. Check that `CONFIG_IDF_TARGET_ESP32C6` is defined in build flags

### Wrong Pin Configuration

**Problem**: Sensors not working on ESP32-C6

**Solution**: The firmware automatically configures pins based on detected board. Verify:
- Board selection in Arduino IDE matches your physical board
- If using a custom board, add a custom board definition

### Upload Issues with ESP32-C6

**Problem**: Cannot upload to Firebeetle 2 ESP32-C6

**Solutions**:
1. Enable "USB CDC On Boot" in Arduino IDE
2. Hold BOOT button while connecting USB
3. Try a different USB cable (must be data cable, not charge-only)
4. Reduce upload speed to 115200

---

## Future Board Support

To add support for additional boards:

1. Add a new board detection block in firmware:
```cpp
#elif CONFIG_IDF_TARGET_ESP32S3
    #define BOARD_TYPE "esp32_s3"
    #define BOARD_NAME "ESP32-S3"
    #define CHIP_MODEL "ESP32-S3"
    // Define pins...
#endif
```

2. Add the pin configuration section
3. Update this documentation
4. Test thoroughly with real hardware

---

## Version History

- **v2.1.0** (Dec 2025): Added multi-board support with automatic detection
  - Added ESP32-C6 support
  - Added board type detection
  - Added board-specific pin configurations
  
- **v2.0.1**: Original ESP32-WROOM-32 only version

---

## Additional Resources

- [ESP32-C6 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf)
- [Firebeetle 2 ESP32-C6 Wiki](https://wiki.dfrobot.com/SKU_DFR0999_FireBeetle_2_Board_ESP32_C6)
- [ESP32 Arduino Core Documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
