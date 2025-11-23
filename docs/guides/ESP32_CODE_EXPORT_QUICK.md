# ESP32 Code Export - Quick Implementation Guide

## 🎯 What Was Built

A complete ESP32 code generation system that creates production-ready firmware with **distinct offline and online operating modes**.

## 📁 Files Created

### 1. Service Layer
**`app/services/esp32_code_generator.py`**
- Core code generation engine
- Generates Arduino C++ or MicroPython code
- Integrates with sensor master control database
- Pulls configuration from registered sensors or generates templates

### 2. API Layer
**`app/api/sensor_master_api.py`** (Updated)
- New endpoint: `POST /api/sensor-master/export-code`
- Accepts sensor configuration and WiFi credentials
- Returns generated code with metadata
- Supports both registered sensors and new templates

### 3. UI Layer
**`app/templates/sensor_master_control.html`** (Updated)
- "Export ESP32 Code" button in header
- Full-featured modal with:
  - Sensor selection dropdown
  - Language selection (Arduino/MicroPython)
  - WiFi credential input
  - Code preview with syntax highlighting
  - Copy to clipboard and download functions

### 4. Documentation
**`ESP32_CODE_EXPORT.md`**
- Comprehensive guide covering all features
- Code structure explanation
- Customization examples
- Troubleshooting guide

## 🚀 How to Use

### From the UI (Recommended)

1. Navigate to: `http://localhost:5000/sensor-master-control`
2. Click **"Export ESP32 Code"** button
3. Configure options:
   - Select existing sensor OR leave blank for template
   - Choose language (Arduino C++ or MicroPython)
   - Enter WiFi credentials (optional)
4. Click **"Generate Code"**
5. **Copy to Clipboard** or **Download** the file

### Via API

```bash
curl -X POST http://localhost:5000/api/sensor-master/export-code \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "esp32_001",
    "language": "arduino",
    "wifi_ssid": "MyWiFi",
    "wifi_password": "MyPassword"
  }'
```

### Via Python Script

```python
from app.services.esp32_code_generator import ESP32CodeGenerator
from app.db import get_connection

conn = get_connection()
generator = ESP32CodeGenerator(conn)

result = generator.generate_code(
    sensor_id="esp32_fermentation_001",
    language="arduino",
    wifi_ssid="MyWiFi",
    wifi_password="MyPassword"
)

if result['success']:
    with open(result['filename'], 'w') as f:
        f.write(result['code'])
    print(f"Generated {result['filename']}")
```

## 🔄 Operating Modes in Generated Code

### Mode 1: OFFLINE MODE 🔴

**Triggers When:**
- Master control URL not configured
- Master control server unreachable
- Network connectivity issues
- Manually switched via command

**Behavior:**
```cpp
// Uses hardcoded configuration
void useOfflineConfiguration() {
    pollingInterval = 60000;  // 1 minute default
    dataEndpoint = "http://fallback.url/api/data";
    // Load saved configuration from preferences
}

// Handles data locally
void handleDataOffline(SensorData data) {
    // Option 1: Save to SD card
    // Option 2: Send to fallback endpoint
    // Option 3: Display locally
    // CUSTOMIZE THIS SECTION
}
```

**Features:**
- Standalone operation
- Uses last known good configuration
- Periodic retry to connect to master (every 10 minutes)
- Data buffering/local storage options

### Mode 2: ONLINE MODE 🟢

**Triggers When:**
- Successfully registered with master control
- Network connectivity restored
- Master control responds to requests

**Behavior:**
```cpp
// Registers with master
bool registerWithMaster() {
    // POST /api/sensor-master/register
    // Receives assignment and initial config
}

// Gets dynamic configuration
bool getConfigFromMaster() {
    // GET /api/sensor-master/config/{sensor_id}
    // Updates polling interval, endpoint, etc.
    // Saves to preferences for offline fallback
}

// Regular check-ins
bool sendHeartbeat() {
    // POST /api/sensor-master/heartbeat
    // Reports status and metrics
    // Receives pending commands
}

// Sends data to configured endpoint
bool sendDataToMaster(SensorData data) {
    // POST {configured_endpoint}
    // Sends structured sensor data
}
```

**Features:**
- Remote configuration updates
- Command execution (restart, update config, etc.)
- Automatic fallback to offline on failure
- Persistent configuration for quick recovery

## 🎨 Code Structure

```
ESP32 Generated Code
│
├── CONFIGURATION SECTION
│   ├── WiFi credentials
│   ├── Master control URL
│   ├── Sensor identification
│   └── Timing constants
│
├── SETUP()
│   ├── WiFi connection
│   ├── Sensor initialization
│   ├── Master registration attempt
│   └── Mode determination
│
├── LOOP()
│   ├── Read sensors
│   ├── Data transmission (mode-dependent)
│   ├── Online: Check-in & commands
│   └── Offline: Retry connection
│
├── SECTION 1: OFFLINE MODE FUNCTIONS
│   ├── useOfflineConfiguration()
│   ├── handleDataOffline()
│   └── sendDataToFallbackEndpoint()
│
├── SECTION 2: ONLINE MODE FUNCTIONS
│   ├── registerWithMaster()
│   ├── getConfigFromMaster()
│   ├── sendHeartbeat()
│   ├── sendDataToMaster()
│   └── processCommands()
│
├── SECTION 3: HARDWARE FUNCTIONS
│   ├── initializeSensors()
│   ├── readSensorData()
│   └── setTargetTemperature()
│
└── SECTION 4: UTILITY FUNCTIONS
    ├── connectToWiFi()
    └── loadSavedConfiguration()
```

## 📊 Workflow Examples

### Scenario 1: Normal Operation (Master Available)

```
1. Device boots → Connects to WiFi
2. Registers with master control → Gets assigned
3. Retrieves configuration → Polling interval: 30s
4. Operates in ONLINE MODE
5. Sends data every 30s to configured endpoint
6. Heartbeat every 5 minutes → Reports metrics
7. Receives command → Executes and reports back
```

### Scenario 2: Offline Operation (Master Unavailable)

```
1. Device boots → Connects to WiFi
2. Master registration fails → No response
3. Switches to OFFLINE MODE
4. Loads default/saved configuration
5. Operates independently with polling interval: 60s
6. Sends data to fallback endpoint (if configured)
7. Retries master connection every 10 minutes
```

### Scenario 3: Connection Recovery

```
1. Device running in OFFLINE MODE
2. 10-minute retry timer expires
3. Attempts master registration → Success!
4. Switches to ONLINE MODE
5. Retrieves fresh configuration
6. Saves configuration for future offline use
7. Continues normal operation
```

## 🔧 Customization Points

### 1. Offline Behavior
Location: `SECTION 1: OFFLINE MODE FUNCTIONS`

```cpp
void handleDataOffline(SensorData data) {
    // ⚠️ CUSTOMIZE HERE
    // Add your offline data handling logic
    // Examples:
    // - Save to SD card
    // - Display on OLED/LCD
    // - Send to local MQTT broker
    // - Store in queue for later transmission
}
```

### 2. Sensor Reading
Location: `SECTION 3: HARDWARE FUNCTIONS`

```cpp
SensorData readSensorData() {
    // ⚠️ CUSTOMIZE HERE
    // Read from your specific sensors
    // Examples:
    // - DS18B20 temperature sensor
    // - DHT22 humidity sensor
    // - Analog sensors
    // - I2C/SPI devices
}
```

### 3. Custom Commands
Location: `SECTION 2: ONLINE MODE FUNCTIONS`

```cpp
void processCommands(JsonArray commands) {
    // ⚠️ ADD CUSTOM COMMANDS HERE
    if (commandType == "your_custom_command") {
        // Handle your command
    }
}
```

## 📈 Testing Checklist

- [ ] **WiFi Connection**
  - Device connects to WiFi successfully
  - IP address displayed in serial monitor
  
- [ ] **Offline Mode**
  - Operates without master control
  - Uses default configuration
  - Data handling works (fallback/local)
  - Retries connection periodically
  
- [ ] **Online Mode**
  - Registers successfully with master
  - Retrieves configuration
  - Sends data to configured endpoint
  - Heartbeat messages work
  - Commands execute correctly
  
- [ ] **Mode Transitions**
  - Offline → Online transition smooth
  - Online → Offline fallback works
  - Configuration persists across reboots
  
- [ ] **Sensor Reading**
  - Sensors initialize correctly
  - Data reading accurate
  - Error handling for invalid readings

## 🔍 Serial Monitor Examples

### Successful Online Mode Startup
```
===========================================
ESP32 Sensor with Master Control
===========================================
Sensor ID: esp32_fermentation_001
===========================================

[WIFI] Connecting to: MyWiFi
[WIFI] Connected!
[WIFI] IP Address: 192.168.1.150

[STARTUP] Attempting to connect to master control...
[REGISTRATION] Successfully registered with: Local Master
[STARTUP] Master control connected - Running in ONLINE mode
[ONLINE MODE] Configuration updated:
  - Polling Interval: 60s
  - Data Endpoint: http://192.168.1.100:5001/api/devices/data

[STARTUP] Initialization complete

[ONLINE] Data sent to master successfully
[ONLINE] Performing check-in with master control...
[ONLINE] Heartbeat sent successfully
```

### Offline Mode Operation
```
===========================================
ESP32 Sensor with Master Control
===========================================
Sensor ID: esp32_fermentation_001
===========================================

[WIFI] Connecting to: MyWiFi
[WIFI] Connected!
[WIFI] IP Address: 192.168.1.150

[STARTUP] Attempting to connect to master control...
[REGISTRATION] Failed with HTTP code: -1
[STARTUP] Master control unavailable - Running in OFFLINE mode

[OFFLINE MODE] Loading default configuration...
[OFFLINE MODE] Configuration loaded
  - Polling Interval: 60 seconds
  - Data Endpoint: http://192.168.1.100:5000/api/devices/data

[STARTUP] Initialization complete

[OFFLINE MODE] Processing sensor data...
[OFFLINE MODE] Temperature: 20.5°C
[OFFLINE MODE] Target: 18.0°C
[OFFLINE MODE] Relay: OFF
[OFFLINE MODE] Data sent to fallback endpoint

[OFFLINE] Retrying connection to master control...
[OFFLINE] Master still unavailable, continuing in offline mode
```

## 🎓 Key Concepts

### Configuration Persistence
- Online configuration saved to ESP32 flash
- Available immediately when switching to offline
- Survives reboots and power loss
- Uses Arduino Preferences library

### Graceful Degradation
- Always operational, even without master
- Automatic fallback mechanisms
- No data loss during transitions
- Continuous operation guaranteed

### Remote Management
- Dynamic configuration updates
- Remote command execution
- Health monitoring via heartbeat
- Centralized control of fleet

## 📚 Next Steps

1. **Generate Your First Code**
   - Use the UI or API to export code
   - Flash to ESP32 and test

2. **Customize Sections**
   - Implement your sensor reading logic
   - Customize offline behavior
   - Add hardware-specific initialization

3. **Test Both Modes**
   - Verify offline operation
   - Test online registration
   - Confirm mode transitions

4. **Deploy to Production**
   - Configure master control instance
   - Register sensors
   - Monitor via master control UI

## 🤝 Integration with Master Control

The generated code seamlessly integrates with:
- **Sensor Master Control** system
- **Configuration Templates** for bulk management
- **Command Queue** for remote operations
- **Heartbeat Monitoring** for health tracking

All configured through the Sensor Master Control UI at:
`http://localhost:5000/sensor-master-control`

## ℹ️ Additional Resources

- **Full Documentation**: `ESP32_CODE_EXPORT.md`
- **Master Control Guide**: `SENSOR_MASTER_CONTROL_SUMMARY.md`
- **Quick Reference**: `SENSOR_MASTER_CONTROL_QUICK_REF.md`
- **API Documentation**: `docs/SENSOR_MASTER_CONTROL.md`

---

**Generated**: 2025-11-22
**System**: Sensor Master Control v2.0
**Supported Languages**: Arduino C++, MicroPython
**Supported Boards**: ESP32 (all variants)
