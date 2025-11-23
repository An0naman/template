# Dynamic Script Updates for ESP32 Sensors

## Overview

The Sensor Master Control system now supports **dynamic script updates** that can be sent to ESP32 devices over WiFi in real-time. This allows you to update device behavior, LED patterns, sensor logic, or any other code without physically accessing the devices.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Web Interface (Flask App)                             │
│  http://localhost:5001/sensor-master-control           │
│                                                         │
│  1. Upload Script via UI                               │
│     ├─ Select target sensor                            │
│     ├─ Paste Arduino/MicroPython code                  │
│     └─ Click "Upload to Sensor"                        │
│                                                         │
│  2. Script stored in database                          │
│     └─ SensorScripts table                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            │
                            │ WiFi
                            ▼
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ESP32 Device                                           │
│                                                         │
│  1. Checks for updates every 30 seconds                │
│     GET /api/sensor-master/script/{sensor_id}          │
│                                                         │
│  2. If new script available:                           │
│     ├─ Downloads script content                        │
│     ├─ Saves to preferences (flash memory)             │
│     └─ Begins executing new script                     │
│                                                         │
│  3. Script persists across reboots                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Features

### ✅ Real-Time Updates
- Scripts are sent over WiFi
- No need to physically access the device
- Updates apply within 30 seconds

### ✅ Persistent Storage
- Scripts saved to ESP32 flash memory
- Survives power cycles and reboots
- Falls back to local script if offline

### ✅ Version Control
- Track script versions (e.g., "1.0.0", "1.2.5")
- View update history
- Rollback capability

### ✅ Multiple Script Types
- **Arduino C++**: Full Arduino code snippets
- **MicroPython**: Python code for MicroPython firmware
- **Snippets**: Small code fragments (functions, loops, etc.)

### ✅ Per-Sensor Configuration
- Upload different scripts to different sensors
- Target specific devices by sensor_id
- Manage fleet of devices individually

## Usage Guide

### Step 1: Access the Web Interface

Navigate to: `http://localhost:5001/sensor-master-control`

### Step 2: Upload a Script

1. **Click "Upload Script"** button
2. **Select Target Sensor** from dropdown (must be registered)
3. **Enter Script Details:**
   - Version (e.g., "1.0.1")
   - Type (Arduino, MicroPython, or Snippet)
   - Description (optional, e.g., "Triple blink pattern")
4. **Paste Your Code** in the text area
5. **Click "Upload to Sensor"**

### Step 3: Wait for Update

- ESP32 checks for updates every 30 seconds
- When in **ONLINE MODE**, it will automatically download
- Script is saved to flash and begins executing
- Check serial monitor to see update confirmation

## Example Scripts

### Example 1: Simple LED Blink Pattern

```cpp
// Triple blink pattern
void executeLocalScript() {
    unsigned long currentTime = millis();
    
    // Fast triple blink, then pause
    if (currentTime - lastBlinkTime < 150) {
        digitalWrite(LED_PIN, HIGH);
    } else if (currentTime - lastBlinkTime < 300) {
        digitalWrite(LED_PIN, LOW);
    } else if (currentTime - lastBlinkTime < 450) {
        digitalWrite(LED_PIN, HIGH);
    } else if (currentTime - lastBlinkTime < 600) {
        digitalWrite(LED_PIN, LOW);
    } else if (currentTime - lastBlinkTime < 750) {
        digitalWrite(LED_PIN, HIGH);
    } else if (currentTime - lastBlinkTime < 900) {
        digitalWrite(LED_PIN, LOW);
    } else if (currentTime - lastBlinkTime >= 2000) {
        lastBlinkTime = currentTime;
    }
}
```

### Example 2: SOS Pattern

```cpp
// SOS Morse code pattern
void executeLocalScript() {
    static int step = 0;
    unsigned long currentTime = millis();
    
    // S = ... (short-short-short)
    // O = --- (long-long-long)
    // S = ... (short-short-short)
    
    const int SHORT = 200;
    const int LONG = 600;
    const int PAUSE = 200;
    const int LETTER_PAUSE = 600;
    
    switch(step) {
        case 0: case 2: case 4: // S dots
            digitalWrite(LED_PIN, HIGH);
            if (currentTime - lastBlinkTime >= SHORT) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 1: case 3: case 5:
            digitalWrite(LED_PIN, LOW);
            if (currentTime - lastBlinkTime >= PAUSE) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 6: // Letter pause after S
            if (currentTime - lastBlinkTime >= LETTER_PAUSE) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 7: case 9: case 11: // O dashes
            digitalWrite(LED_PIN, HIGH);
            if (currentTime - lastBlinkTime >= LONG) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 8: case 10: case 12:
            digitalWrite(LED_PIN, LOW);
            if (currentTime - lastBlinkTime >= PAUSE) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 13: // Letter pause after O
            if (currentTime - lastBlinkTime >= LETTER_PAUSE) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 14: case 16: case 18: // S dots again
            digitalWrite(LED_PIN, HIGH);
            if (currentTime - lastBlinkTime >= SHORT) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 15: case 17: case 19:
            digitalWrite(LED_PIN, LOW);
            if (currentTime - lastBlinkTime >= PAUSE) {
                lastBlinkTime = currentTime;
                step++;
            }
            break;
        case 20: // Long pause before repeat
            if (currentTime - lastBlinkTime >= 2000) {
                lastBlinkTime = currentTime;
                step = 0; // Restart
            }
            break;
    }
}
```

### Example 3: Breathing LED Effect

```cpp
// Smooth breathing effect
void executeLocalScript() {
    static int brightness = 0;
    static int fadeAmount = 5;
    
    brightness += fadeAmount;
    
    if (brightness <= 0 || brightness >= 255) {
        fadeAmount = -fadeAmount;
    }
    
    analogWrite(LED_PIN, brightness);
    delay(30);
}
```

### Example 4: Temperature-Based Alert

```cpp
// Rapid blink when temperature is high
void executeLocalScript() {
    SensorData data = readSensorData();
    
    if (data.temperature > 30.0) {
        // Rapid blink = alert
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        delay(100);
    } else if (data.temperature > 25.0) {
        // Medium blink = warning
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        delay(500);
    } else {
        // Slow blink = normal
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        delay(1000);
    }
}
```

## ESP32 Integration

Your ESP32 code already has the necessary integration! Here's what's happening:

### 1. Automatic Script Checking (Online Mode)

```cpp
// In loop()
if (currentMode == MODE_ONLINE && currentTime - lastScriptCheck >= scriptCheckInterval) {
    lastScriptCheck = currentTime;
    checkForScriptUpdates();  // Checks every 30 seconds
}
```

### 2. Script Download and Storage

```cpp
bool checkForScriptUpdates() {
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/script/" + String(SENSOR_ID);
    http.begin(url);
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        // Parse response and extract script
        String newScript = doc["script"].as<String>();
        String scriptVersion = doc["version"].as<String>();
        
        // Save to flash memory
        preferences.putString("serverScript", newScript);
        preferences.putString("scriptVersion", scriptVersion);
        
        currentScript = newScript;
        hasServerScript = true;
    }
}
```

### 3. Script Execution

```cpp
// When in ONLINE mode, execute server script
// When in OFFLINE mode, execute local fallback
if (currentMode == MODE_OFFLINE) {
    executeLocalScript();  // Your local fallback
}
```

## API Endpoints

### Upload Script
```
POST /api/sensor-master/script
Content-Type: application/json

{
    "sensor_id": "esp32_fermentation_001",
    "script_content": "void executeLocalScript() { ... }",
    "script_version": "1.0.0",
    "script_type": "arduino",
    "description": "LED blink pattern"
}
```

### Get Script for Sensor (ESP32 calls this)
```
GET /api/sensor-master/script/{sensor_id}

Response:
{
    "script_available": true,
    "script": "void executeLocalScript() { ... }",
    "version": "1.0.0",
    "type": "arduino",
    "updated_at": "2025-11-22 01:30:00"
}
```

### List All Scripts
```
GET /api/sensor-master/scripts?sensor_id=esp32_001

Response: [
    {
        "id": 1,
        "sensor_id": "esp32_001",
        "script_content": "...",
        "script_version": "1.0.0",
        "script_type": "arduino",
        "is_active": 1,
        ...
    }
]
```

## Testing the Feature

### Test with cURL

#### 1. Upload a script
```bash
curl -X POST http://localhost:5001/api/sensor-master/script \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "esp32_fermentation_001",
    "script_content": "void executeLocalScript() { digitalWrite(2, HIGH); delay(100); digitalWrite(2, LOW); delay(900); }",
    "script_version": "1.0.0",
    "script_type": "arduino",
    "description": "Quick blink test"
  }'
```

#### 2. Verify script is available
```bash
curl http://localhost:5001/api/sensor-master/script/esp32_fermentation_001
```

### Monitor ESP32 Serial Output

When the script is received, you'll see:
```
📜 New script received from server:
  Version: 1.0.0
  Script length: 95 bytes
```

## Workflow Diagram

```
Developer                    Web App                     ESP32
    │                           │                          │
    │  1. Upload Script         │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │                           │  Store in                │
    │                           │  Database                │
    │                           │                          │
    │                           │      2. Poll for updates │
    │                           │<─────────────────────────┤
    │                           │                          │
    │                           │  3. Send script          │
    │                           ├─────────────────────────>│
    │                           │                          │
    │                           │                          │  4. Save to flash
    │                           │                          │  5. Execute script
    │                           │                          │
    │                           │      6. Confirmation     │
    │                           │<─────────────────────────┤
    │                           │                          │
```

## Best Practices

### ✅ DO:
- Test scripts locally before uploading
- Use version numbers (1.0.0, 1.0.1, etc.)
- Add descriptions for each script
- Keep scripts focused and simple
- Monitor serial output after upload

### ❌ DON'T:
- Upload untested code to production devices
- Use very large scripts (memory limited)
- Change critical sensor logic without testing
- Forget to handle timing/delays properly
- Upload scripts that could brick the device

## Troubleshooting

### Script Not Updating?

1. **Check sensor is in ONLINE MODE**
   - Serial monitor should show "ONLINE MODE"
   - WiFi must be connected
   - Master control must be reachable

2. **Wait 30 seconds**
   - Script check interval is 30 seconds
   - Be patient for automatic update

3. **Verify script was uploaded**
   ```bash
   curl http://localhost:5001/api/sensor-master/script/YOUR_SENSOR_ID
   ```

4. **Check ESP32 serial monitor**
   - Look for "New script received" message
   - Check for any error messages

### Script Not Executing?

1. **Check script syntax**
   - Must be valid Arduino C++ or MicroPython
   - Verify no compilation errors

2. **Check mode**
   - Scripts execute only when conditions are met
   - In OFFLINE mode, local fallback runs
   - In ONLINE mode, server script should run

3. **Check timing**
   - Make sure `executeLocalScript()` is being called
   - Verify loop() timing isn't blocking execution

## Security Considerations

- **Script validation**: Consider adding syntax checking before upload
- **Access control**: Restrict who can upload scripts
- **Script signing**: Future enhancement for cryptographic verification
- **Size limits**: Limit script size to prevent memory issues
- **Rate limiting**: Prevent excessive script updates

## Future Enhancements

- [ ] Script validation before upload
- [ ] Script history and rollback
- [ ] Scheduled script updates
- [ ] Script templates library
- [ ] Bulk upload to multiple sensors
- [ ] Script diff viewer
- [ ] Automatic backup of previous scripts
- [ ] Script testing simulator

## Summary

You can now:
1. ✅ Upload Arduino or MicroPython scripts via web interface
2. ✅ Send scripts to ESP32 devices over WiFi
3. ✅ Update device behavior without physical access
4. ✅ Manage scripts per sensor
5. ✅ Track versions and descriptions
6. ✅ Scripts persist across reboots

Your ESP32 devices will automatically check for and apply script updates every 30 seconds when in ONLINE mode!
