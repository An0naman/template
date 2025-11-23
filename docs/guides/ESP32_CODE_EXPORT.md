# ESP32 Code Export Feature - Documentation

## Overview

The ESP32 Code Export feature generates production-ready firmware code for ESP32 devices that integrates with the Sensor Master Control system. The generated code includes **two distinct operating modes** to ensure your sensors can operate reliably in any situation.

## 🎯 Key Features

### Dual Operating Modes

#### 1. **OFFLINE MODE** 🔴
- Runs when the device **cannot connect** to master control
- Uses local/fallback configuration
- Operates independently with hardcoded or saved settings
- Stores data locally or sends to fallback endpoints
- **Perfect for:** Development, testing, network outages, standalone operation

#### 2. **ONLINE MODE** 🟢
- Runs when connected to master control
- Receives dynamic configuration from the server
- Reports status and metrics via heartbeat
- Executes remote commands
- **Perfect for:** Production deployment, centralized management, remote updates

### Automatic Transitions
- Device automatically attempts to connect to master control on startup
- If unavailable, operates in **OFFLINE MODE**
- Periodically retries connection (every 10 minutes)
- **Seamlessly switches** from offline to online when connection is restored
- Configuration persists between reboots

## 🚀 Quick Start

### Step 1: Access Code Export

1. Navigate to **Sensor Master Control** page
2. Click the **"Export ESP32 Code"** button
3. The code export modal will open

### Step 2: Configure Export Options

**Option 1: Generate Template (New Sensor)**
- Leave "Sensor" dropdown as "Generate New Template"
- Enter sensor type (e.g., `esp32_fermentation`)
- Select language (Arduino C++ or MicroPython)
- Enter WiFi credentials
- Click "Generate Code"

**Option 2: Export for Existing Sensor**
- Select an existing registered sensor from dropdown
- Configuration will be pre-populated from registration
- Enter WiFi credentials
- Click "Generate Code"

### Step 3: Download and Flash

1. **Copy to Clipboard** or **Download** the generated code
2. Open in Arduino IDE or upload to ESP32
3. Flash to your ESP32 device
4. Monitor serial output to see mode transitions

## 📋 Generated Code Structure

### Arduino C++ Structure

```
┌─────────────────────────────────────────────────┐
│ CONFIGURATION SECTION                           │
│ - WiFi credentials                              │
│ - Master control URL                            │
│ - Sensor ID and type                            │
│ - Timing intervals                              │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ SETUP() - INITIALIZATION                        │
│ - Connect to WiFi                               │
│ - Initialize sensors                            │
│ - Attempt master control registration           │
│ - Determine initial mode (OFFLINE/ONLINE)       │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ LOOP() - MAIN PROGRAM                           │
│                                                 │
│ ┌─────────────────────────────────────┐        │
│ │ Read Sensor Data                    │        │
│ └─────────────────────────────────────┘        │
│           ↓                                     │
│ ┌─────────────────────────────────────┐        │
│ │ DATA TRANSMISSION                   │        │
│ │  ┌──────────────┐  ┌──────────────┐ │        │
│ │  │ OFFLINE MODE │  │ ONLINE MODE  │ │        │
│ │  │ Send to      │  │ Send to      │ │        │
│ │  │ fallback or  │  │ master       │ │        │
│ │  │ store local  │  │ endpoint     │ │        │
│ │  └──────────────┘  └──────────────┘ │        │
│ └─────────────────────────────────────┘        │
│           ↓                                     │
│ ┌─────────────────────────────────────┐        │
│ │ ONLINE MODE: Check-in & Commands    │        │
│ └─────────────────────────────────────┘        │
│           ↓                                     │
│ ┌─────────────────────────────────────┐        │
│ │ OFFLINE MODE: Retry Connection      │        │
│ └─────────────────────────────────────┘        │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Code Sections to Customize

The generated code includes **clearly marked sections** for customization:

#### 🔧 Section 1: OFFLINE MODE Functions
```cpp
// ============================================================================
// SECTION 1: OFFLINE MODE FUNCTIONS
// ============================================================================
// CUSTOMIZE THIS SECTION FOR YOUR OFFLINE BEHAVIOR

void useOfflineConfiguration() {
    // Set default polling interval
    // Configure fallback endpoints
    // Load saved configuration
}

void handleDataOffline(SensorData data) {
    // Option 1: Save to SD card
    // Option 2: Send to fallback endpoint
    // Option 3: Display locally
}
```

#### 🌐 Section 2: ONLINE MODE Functions
```cpp
// ============================================================================
// SECTION 2: ONLINE MODE FUNCTIONS
// ============================================================================
// These functions handle master control integration

bool registerWithMaster() { ... }
bool getConfigFromMaster() { ... }
bool sendHeartbeat() { ... }
bool sendDataToMaster(SensorData data) { ... }
void processCommands(JsonArray commands) { ... }
```

#### ⚙️ Section 3: Hardware & Sensor Functions
```cpp
// ============================================================================
// SECTION 3: HARDWARE & SENSOR FUNCTIONS
// ============================================================================
// CUSTOMIZE THIS SECTION FOR YOUR HARDWARE

void initializeSensors() {
    // Initialize temperature sensor, relays, etc.
}

SensorData readSensorData() {
    // Read from your specific sensors
    // Return structured data
}
```

## 🔄 Operating Mode Details

### OFFLINE MODE Behavior

When the ESP32 cannot connect to master control:

1. **Configuration**
   - Uses hardcoded default values
   - Loads last saved configuration from preferences
   - Polling interval: 60 seconds (default)
   - Endpoint: Fallback or local storage

2. **Data Handling Options**
   ```cpp
   // Option A: Send to fallback endpoint
   sendDataToFallbackEndpoint(data);
   
   // Option B: Store locally (SD card/SPIFFS)
   saveDataLocally(data);
   
   // Option C: Display only (serial/screen)
   displayDataLocally(data);
   ```

3. **Retry Mechanism**
   - Attempts to connect to master every **10 minutes**
   - Automatic transition to ONLINE mode on success
   - No disruption to data collection

### ONLINE MODE Behavior

When connected to master control:

1. **Registration**
   ```cpp
   POST /api/sensor-master/register
   {
     "sensor_id": "esp32_001",
     "sensor_type": "esp32_fermentation",
     "capabilities": ["temperature", "relay_control"]
   }
   ```

2. **Configuration Retrieval**
   ```cpp
   GET /api/sensor-master/config/esp32_001
   ```
   - Receives polling interval
   - Receives data endpoint
   - Receives sensor mappings
   - Saves to preferences for offline fallback

3. **Heartbeat (Every 5 minutes)**
   ```cpp
   POST /api/sensor-master/heartbeat
   {
     "sensor_id": "esp32_001",
     "status": "online",
     "metrics": {
       "uptime": 3600,
       "free_memory": 120000,
       "wifi_rssi": -65
     }
   }
   ```

4. **Command Processing**
   - `update_config`: Re-fetch configuration
   - `restart`: Reboot ESP32
   - `set_target_temp`: Update target temperature
   - Custom commands as needed

## 📊 Data Flow Examples

### Example 1: Startup with Available Master

```
[STARTUP] Connecting to WiFi...
[WIFI] Connected! IP: 192.168.1.150
[STARTUP] Attempting to connect to master control...
[REGISTRATION] Successfully registered with: Local Master
[STARTUP] Master control connected - Running in ONLINE mode
[ONLINE MODE] Configuration updated:
  - Polling Interval: 60s
  - Data Endpoint: http://192.168.1.100:5001/api/devices/data
[ONLINE] Data sent to master successfully
```

### Example 2: Startup without Master Control

```
[STARTUP] Connecting to WiFi...
[WIFI] Connected! IP: 192.168.1.150
[STARTUP] Attempting to connect to master control...
[REGISTRATION] Failed with HTTP code: -1
[STARTUP] Master control unavailable - Running in OFFLINE mode
[OFFLINE MODE] Loading default configuration...
[OFFLINE MODE] Using saved endpoint: http://192.168.1.100:5000/api/devices/data
[OFFLINE MODE] Temperature: 20.5°C
[OFFLINE MODE] Data sent to fallback endpoint
```

### Example 3: Transition from Offline to Online

```
[OFFLINE] Retrying connection to master control...
[REGISTRATION] Successfully registered with: Local Master
[OFFLINE->ONLINE] Successfully connected to master control!
[ONLINE MODE] Configuration updated:
  - Polling Interval: 30s
  - Data Endpoint: http://192.168.1.100:5001/api/devices/data
[ONLINE] Data sent to master successfully
```

## 🎛️ Configuration Options

### WiFi Configuration
```cpp
const char* WIFI_SSID = "YourWiFiSSID";
const char* WIFI_PASSWORD = "YourWiFiPassword";
```

### Master Control URL
```cpp
const char* MASTER_CONTROL_URL = "http://192.168.1.100:5000";
```
- Use your server's IP address or domain
- Include port if not using standard HTTP (80)
- Leave blank or use placeholder for offline-only operation

### Sensor Identification
```cpp
const char* SENSOR_ID = "esp32_fermentation_001";
const char* SENSOR_TYPE = "esp32_fermentation";
const char* SENSOR_NAME = "Fermentation Chamber 1";
```
- `SENSOR_ID`: Must be unique across all sensors
- `SENSOR_TYPE`: Groups sensors with similar configuration
- `SENSOR_NAME`: Human-readable name

### Timing Configuration
```cpp
const unsigned long CHECK_IN_INTERVAL = 300000;     // 5 minutes
const unsigned long DATA_SEND_INTERVAL = 60000;     // 1 minute
const unsigned long MASTER_RETRY_INTERVAL = 600000; // 10 minutes
```

## 🔌 API Endpoints Used

### Registration (Phone-Home)
```
POST /api/sensor-master/register
```
Registers the sensor with master control and receives assignment.

### Configuration Retrieval
```
GET /api/sensor-master/config/{sensor_id}
```
Retrieves current configuration, including any updates.

### Heartbeat
```
POST /api/sensor-master/heartbeat
```
Reports sensor status and receives pending commands.

### Data Submission (Configured Endpoint)
```
POST {configured_endpoint}
```
Sends sensor data to the endpoint specified in configuration.

## 🛠️ Customization Guide

### Adding New Sensor Types

1. **Update Hardware Initialization**
   ```cpp
   void initializeSensors() {
       // Add your sensor initialization
       pinMode(NEW_SENSOR_PIN, INPUT);
   }
   ```

2. **Update Data Reading**
   ```cpp
   SensorData readSensorData() {
       data.newSensorValue = readNewSensor();
       return data;
   }
   ```

3. **Update Data Structure**
   ```cpp
   struct SensorData {
       float temperature;
       float newSensorValue;  // Add new field
       bool valid;
   };
   ```

### Customizing Offline Behavior

```cpp
void handleDataOffline(SensorData data) {
    // Example: Store to SD card
    File dataFile = SD.open("/data.txt", FILE_APPEND);
    if (dataFile) {
        dataFile.printf("%lu,%.2f,%.2f\n", 
                       millis(), 
                       data.temperature, 
                       data.targetTemp);
        dataFile.close();
    }
    
    // Example: Display on OLED
    display.clearDisplay();
    display.printf("Temp: %.1f C\n", data.temperature);
    display.display();
}
```

### Adding Custom Commands

```cpp
void processCommands(JsonArray commands) {
    for (JsonObject cmd : commands) {
        String commandType = cmd["command_type"];
        
        // Add your custom command
        if (commandType == "calibrate_sensor") {
            float offset = cmd["command_data"]["offset"];
            calibrateSensor(offset);
        }
    }
}
```

## 📡 Testing the Code

### Test Offline Mode

1. Comment out or set invalid master control URL:
   ```cpp
   const char* MASTER_CONTROL_URL = "";
   ```

2. Flash and monitor serial output
3. Verify device operates in OFFLINE mode
4. Check data handling (fallback/local storage)

### Test Online Mode

1. Set valid master control URL
2. Ensure master control server is running
3. Flash and monitor serial output
4. Verify registration and configuration retrieval
5. Check data appears in master control

### Test Mode Transition

1. Start with master control running (ONLINE mode)
2. Stop master control server
3. Wait for heartbeat timeout (~5 minutes)
4. Verify device continues operating
5. Restart master control
6. Wait for retry interval (~10 minutes)
7. Verify automatic reconnection

## 🐛 Troubleshooting

### Device Won't Connect to WiFi
- Check SSID and password
- Verify WiFi signal strength
- Check router settings (2.4GHz vs 5GHz)
- ESP32 supports only 2.4GHz WiFi

### Can't Register with Master Control
- Verify master control URL is correct
- Check network connectivity (ping server)
- Ensure master control service is running
- Check firewall rules
- Verify API endpoint `/api/sensor-master/register`

### Data Not Appearing in Master Control
- Check configured data endpoint in master control
- Verify sensor is registered and has configuration
- Check master control logs for errors
- Verify data format matches expected structure

### Device Keeps Switching Modes
- Check network stability
- Increase heartbeat timeout
- Check master control server health
- Verify no firewall blocking

### Configuration Not Persisting
- Check if Preferences library is working
- Verify flash memory is not corrupted
- Increase delay between writes
- Check for adequate free memory

## 📚 Language-Specific Notes

### Arduino C++

**Required Libraries:**
- WiFi.h (built-in)
- HTTPClient.h (built-in)
- ArduinoJson (install via Library Manager)
- Preferences.h (built-in)

**Board Settings:**
- Board: ESP32 Dev Module
- Upload Speed: 921600
- Flash Frequency: 80MHz
- Partition Scheme: Default 4MB

### MicroPython

**Required Modules:**
- network (built-in)
- urequests (built-in)
- ujson (built-in)
- machine (built-in)

**Installation:**
1. Flash MicroPython firmware to ESP32
2. Upload generated `.py` file
3. Run: `python main.py`

## 🚀 Advanced Features

### Persistent Configuration

Both modes save configuration to non-volatile storage:
```cpp
preferences.putString("dataEndpoint", dataEndpoint);
preferences.putULong("pollingInterval", pollingInterval);
```

This ensures:
- Configuration survives reboots
- Offline mode can use last known good config
- Faster startup on subsequent boots

### Command Queue Processing

Master control can queue commands for execution:
- `update_config`: Refresh configuration
- `restart`: Reboot device
- `set_target_temp`: Update temperature target
- Custom commands via JSON payload

### Metrics Reporting

Device reports health metrics in heartbeat:
- Uptime in seconds
- Free heap memory
- WiFi signal strength (RSSI)
- Custom metrics as needed

## 📖 Related Documentation

- [Sensor Master Control Summary](SENSOR_MASTER_CONTROL_SUMMARY.md)
- [Sensor Master Control Quick Reference](SENSOR_MASTER_CONTROL_QUICK_REF.md)
- [API Documentation](docs/SENSOR_MASTER_CONTROL.md)

## 🤝 Support

For issues or questions:
1. Check serial monitor output
2. Review master control logs
3. Test with provided examples
4. Verify API endpoints with cURL

## 📄 License

This generated code is part of the template project and inherits its license.
