# FireBeetle 2 ESP32-C6 Sensor Firmware

## Overview

This firmware enables the DFRobot FireBeetle 2 ESP32-C6 (SKU DFR1075) to function as a configurable IoT sensor device with web-based management capabilities. The device can monitor various sensors, control actuators, execute logic rules, and report data to a central server.

**Hardware**: [DFRobot FireBeetle 2 ESP32-C6](https://wiki.dfrobot.com/SKU_DFR1075_FireBeetle_2_Board_ESP32_C6)

## Features

### Core Capabilities
- **Dynamic Logic System**: Execute complex conditional logic rules stored in JSON format
- **Multi-Sensor Support**: Read from digital/analog sensors, I2C devices, and more
- **Actuator Control**: Control relays, servos, motors, and other output devices
- **Web Interface**: Built-in web server for device configuration and monitoring
- **OTA Updates**: Over-The-Air firmware updates via web interface
- **Battery Monitoring**: Accurate LiPo battery voltage and percentage monitoring
- **Heartbeat Detection**: Automatic reconnection if server becomes unavailable
- **WiFi Management**: Connect to configured WiFi networks with fallback AP mode

### Supported Actions
- **Sensors**: Digital read, analog read, I2C communication, DHT sensors
- **Actuators**: Digital write, PWM, servo control, motor drivers
- **Logic**: Conditional execution (if/else), timers, delays
- **Communication**: HTTP requests, data logging, variable storage
- **Battery**: Read voltage and percentage with calibrated voltage divider

## Hardware Configuration

### Battery Monitoring (Firebeetle 2 ESP32-C6 Specific)

The board has a built-in voltage divider on **GPIO 0** for battery monitoring:

```cpp
#define BATTERY_PIN 0  // GPIO 0 is the battery detection pin

// Calibrated voltage divider values
float r1 = 145900.0;  // R1 = 145.9kΩ (calibrated)
float r2 = 100000.0;  // R2 = 100kΩ
float vref = 3.3;     // ADC reference voltage
```

**Calibration Notes**:
- Calibrated at 3.97V and 4.15V actual battery voltage
- Accuracy: ±0.05V across 3.3V-4.2V LiPo range
- ADC: 12-bit resolution with 12dB attenuation (0-3.3V range)
- Sampling: 50-sample averaging with outlier removal (discard min/max)

**Available Variables**:
- `{battery}` - Battery voltage in volts (e.g., 4.15)
- `{battery_pct}` - Battery percentage 0-100% (e.g., 94)
- `{battery_raw}` - Raw ADC reading 0-4095
- `{battery_vout}` - Voltage at GPIO pin after divider

### Pin Configuration

Refer to the [official FireBeetle 2 ESP32-C6 pinout](https://wiki.dfrobot.com/SKU_DFR1075_FireBeetle_2_Board_ESP32_C6) for detailed pin mapping.

**Important Pins**:
- GPIO 0: Battery voltage detection (built-in voltage divider)
- GPIO 2-7: General purpose I/O
- GPIO 8, 9: I2C (SDA, SCL)
- Built-in LED for status indication

## File Structure

```
firmware/firebeetle_esp32c6/
├── README.md                    # This file
├── sensor_firmware.ino          # Main firmware code (2100+ lines)
├── esp32_web_interface.h        # Web interface HTML/JavaScript
├── platformio.ini               # PlatformIO configuration
└── LOGIC_EXAMPLES.md           # Example logic configurations
```

## Building and Flashing

### Prerequisites
- [PlatformIO](https://platformio.org/) installed
- USB-C cable for programming
- FireBeetle 2 ESP32-C6 board

### Using PlatformIO

1. **Open the project**:
   ```bash
   cd firmware/firebeetle_esp32c6
   ```

2. **Build the firmware**:
   ```bash
   pio run -e firebeetle2_esp32c6
   ```

3. **Upload to device**:
   ```bash
   pio run -e firebeetle2_esp32c6 -t upload
   ```

4. **Monitor serial output**:
   ```bash
   pio device monitor
   ```

### PlatformIO Troubleshooting

#### Build Fails or Platform Corruption
If you encounter build errors, corrupted packages, or persistent compilation issues:

```bash
# Remove all cached packages and platforms
rm -rf ~/.platformio/packages
rm -rf ~/.platformio/platforms

# Reinstall everything fresh
pio run -e firebeetle2_esp32c6
```

This forces PlatformIO to download fresh packages and platform files.

#### Upload Port Not Found
```bash
# List available serial ports
pio device list

# If device not showing:
# 1. Check USB cable (must support data, not just charging)
# 2. Check driver installation (CP210x or CH340 depending on board)
# 3. Try different USB port
# 4. On Linux: Add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login again
```

#### Permissions Denied on Linux
```bash
# Give temporary access to serial port
sudo chmod 666 /dev/ttyUSB0  # or ttyACM0

# Or permanent fix: add to dialout group (see above)
```

#### Clean Build (When Changes Not Detected)
```bash
# Clean build files
pio run -t clean

# Full clean including dependencies
rm -rf .pio/

# Then rebuild
pio run -e firebeetle2_esp32c6
```

#### Monitor Shows Garbled Output
```bash
# Ensure correct baud rate (default 115200)
pio device monitor --baud 115200

# If still garbled, try:
pio device monitor --baud 115200 --raw
```

### Build Environments

The `platformio.ini` supports multiple build configurations:

- **firebeetle2_esp32c6**: For FireBeetle 2 ESP32-C6 boards
- **esp32_wroom32**: For generic ESP32-WROOM-32 boards

## Initial Setup

### 1. First Boot (AP Mode)

On first boot, the device creates a WiFi access point:

- **SSID**: `ESP32-Setup-XXXXXX` (where XXXXXX is part of MAC address)
- **Password**: `12345678`
- **Web Interface**: http://192.168.4.1

### 2. WiFi Configuration

1. Connect to the ESP32 AP
2. Open http://192.168.4.1
3. Navigate to WiFi settings
4. Enter your WiFi credentials
5. Device will restart and connect to your network

### 3. Finding the Device

Once connected to your network:
- Check your router's DHCP client list
- Look for hostname: `ESP32-XXXXXX`
- Access via: http://[device-ip-address]

## Web Interface

The built-in web interface provides:

### Configuration Pages
- **WiFi Settings**: Configure network credentials
- **Device Settings**: Set device name, heartbeat interval
- **GPIO Configuration**: Set pin modes
- **Logic Editor**: Create and edit logic rules

### Monitoring
- **Status Dashboard**: View sensor readings in real-time
- **Battery Status**: Voltage and percentage (Firebeetle only)
- **Connection Status**: WiFi signal strength, uptime
- **Variable Inspector**: View all global variables

### Maintenance
- **OTA Updates**: Upload new firmware via web browser
- **Restart Device**: Soft reboot without physical access
- **Factory Reset**: Clear all settings (requires physical button)

## Logic System

The firmware uses a JSON-based logic system for defining sensor reading and actuator control behaviors.

### Logic Structure

```json
{
  "alias": "temperature_monitor",
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "if",
      "condition": "{temp} > 25",
      "then": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1
        },
        {
          "type": "log",
          "message": "Temperature high: {temp}°C, fan ON"
        }
      ],
      "else": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0
        }
      ]
    }
  ]
}
```

### Supported Action Types

#### Sensor Reading
- `read_digital`: Read digital pin (HIGH/LOW)
- `read_analog`: Read analog pin (0-4095)
- `read_dht22`: Read DHT22 temperature/humidity sensor
- `read_dht11`: Read DHT11 temperature/humidity sensor
- `read_battery`: Read battery voltage and percentage (Firebeetle)

#### Actuator Control
- `digital_write`: Set digital pin HIGH or LOW
- `analog_write`: Set PWM duty cycle (0-255)
- `servo_write`: Control servo position (0-180 degrees)

#### Logic Control
- `if`: Conditional execution with condition evaluation
- `delay`: Wait for specified milliseconds
- `loop`: Repeat actions N times

#### Communication
- `log`: Write message to serial and/or server
- `http_get`: Make HTTP GET request
- `http_post`: Make HTTP POST request

#### Variables
- `set_variable`: Store value in global variable
- `get_variable`: Retrieve value from global variable

### Variable System

Variables can be used in conditions and messages using `{variable_name}` syntax:

```json
{
  "type": "log",
  "message": "Battery: {battery}V ({battery_pct}%)"
}
```

**Built-in Variables** (on Firebeetle):
- `{battery}`: Battery voltage
- `{battery_pct}`: Battery percentage
- `{battery_raw}`: Raw ADC reading
- `{battery_vout}`: Voltage divider output

## API Endpoints

The device exposes several HTTP endpoints:

### Status Endpoints
- `GET /` - Web interface home page
- `GET /status` - JSON status report
- `GET /variables` - All global variables as JSON

### Configuration Endpoints
- `POST /wifi` - Set WiFi credentials
- `POST /logic` - Upload logic configuration
- `POST /settings` - Update device settings

### Control Endpoints
- `POST /restart` - Restart the device
- `POST /factory_reset` - Reset to factory defaults
- `POST /ota` - Upload firmware update

## Server Communication

### Heartbeat System

The device periodically sends heartbeat messages to the configured server:

```json
{
  "device_id": "ESP32-AABBCC",
  "status": "online",
  "uptime": 3600,
  "rssi": -45,
  "free_heap": 123456,
  "battery_voltage": 4.15,
  "battery_pct": 94
}
```

**Configuration**:
- Default interval: 60 seconds
- Configurable via web interface
- Automatic reconnection on server failure

### Data Logging

Sensor readings can be automatically sent to the server:

```json
{
  "device_id": "ESP32-AABBCC",
  "timestamp": 1735500000,
  "data": {
    "temperature": 25.5,
    "humidity": 60.0,
    "battery": 4.15
  }
}
```

## Troubleshooting

### Device Won't Connect to WiFi
1. Ensure WiFi credentials are correct (case-sensitive)
2. Check if 2.4GHz network (ESP32 doesn't support 5GHz)
3. Reset to AP mode: Hold boot button, restart device

### Battery Reading Inaccurate
1. Verify you're using GPIO 0 (not another pin)
2. Check if battery is actually connected
3. Recalibrate if needed (see Battery Monitoring section)
4. Use `{battery_raw}` to check ADC is working (should be ~2048 at ~4V)

### OTA Update Fails
1. Ensure firmware file is correct `.bin` format
2. Check available heap memory (need >100KB free)
3. Use stable WiFi connection (avoid long distance)
4. Try uploading smaller updates if memory constrained

### Logic Not Executing
1. Check serial monitor for JSON parsing errors
2. Verify JSON syntax (use online validator)
3. Ensure pin modes are set correctly
4. Check if conditions are evaluating as expected

### Web Interface Not Loading
1. Verify device IP address (check router DHCP table)
2. Try accessing via http:// (not https://)
3. Clear browser cache
4. Check if device is in AP mode vs station mode

## Development

### Adding New Action Types

1. Define the action type in `executeAction()`:

```cpp
if (action["type"] == "my_custom_action") {
  // Your implementation here
  int pin = action["pin"];
  // ... do something ...
  return true;
}
```

2. Add to the web interface action list in `esp32_web_interface.h`

3. Document in `LOGIC_EXAMPLES.md`

### Debugging

Enable verbose logging:

```cpp
#define DEBUG_ENABLED true

// Add debug prints
if (DEBUG_ENABLED) {
  Serial.println("Debug: " + message);
}
```

Monitor via serial:
```bash
pio device monitor --baud 115200
```

## Performance Characteristics

- **Boot Time**: ~3-5 seconds
- **WiFi Connection**: ~5-10 seconds
- **Logic Execution**: <1ms per simple action
- **Web Response Time**: <100ms for status pages
- **Memory Usage**: ~150KB RAM typical, ~1MB flash
- **Power Consumption**: 
  - Active (WiFi): ~80-150mA
  - Deep sleep: ~10µA (if implemented)
  - Battery life: ~24-48 hours on 1000mAh LiPo (depends on usage)

## Security Considerations

⚠️ **Important**: This firmware is designed for trusted local networks only.

**Current Limitations**:
- No HTTPS/TLS encryption
- No authentication on web interface
- No encrypted storage of credentials
- No firmware signature verification

**Recommendations**:
- Use on isolated IoT network segment
- Don't expose device directly to internet
- Use VPN for remote access
- Change default AP password immediately

## License

[Your License Here]

## Credits

- Built for DFRobot FireBeetle 2 ESP32-C6
- Uses Arduino framework and ESP32 Arduino core
- ArduinoJson library for JSON parsing
- Community contributions welcome

## Support

For issues, questions, or contributions:
- GitHub Issues: [Your Repo URL]
- Documentation: [Your Docs URL]
- Hardware Reference: https://wiki.dfrobot.com/SKU_DFR1075_FireBeetle_2_Board_ESP32_C6

---

**Last Updated**: December 29, 2025
**Firmware Version**: See `VERSION` file
**Compatible Board**: FireBeetle 2 ESP32-C6 (DFR1075)
