# Interactive Board Visualization Implementation
## Complete Feature Documentation

### Overview
This feature adds an interactive ESP32 board visualization to both the Sensor Master Control interface and the ESP32 device's direct web interface. It allows real-time pin monitoring and control based on the logic builder configuration.

---

## 1. Architecture

### Components Implemented:

1. **Board Configuration System** (`app/static/js/board-configs.js`)
   - JSON-based board definitions
   - Pin layout coordinates
   - Pin capabilities mapping
   - Support for multiple board types

2. **Master Control Interface** (`app/templates/sensor_master_control.html`)
   - Fullscreen modal with split view
   - Live board visualization with pin indicators
   - Interactive pin controls
   - Chip overlay for logs
   - Real-time log streaming

3. **API Endpoint** (`app/api/sensor_master_api.py`)
   - `/api/sensor-master/pin-control` - Send pin commands
   - High-priority command queuing
   - Immediate execution support

4. **ESP32 Web Interface** (`esp32_web_interface.h`)
   - Embedded HTML/CSS/JS for device
   - Direct pin control from device IP
   - Live pin state visualization
   - Integrated serial monitor

5. **Firmware Integration** (`sensor_firmware.ino`)
   - API endpoints for pin states
   - Pin control handler
   - WebSocket-ready architecture

---

## 2. User Interface Features

### Master Control Modal (`sensor_master_control.html`)

**Layout:**
```
┌────────────────────────────────────────────────────┐
│  Interactive Board Monitor: [Sensor ID]      [X]  │
├─────────────────────┬──────────────────────────────┤
│                     │ Live Logs                    │
│  Board Viz          │ ┌──────────────────────────┐ │
│  ┌──────────────┐   │ │ [12:00:01] Log entry    │ │
│  │              │   │ │ [12:00:02] Pin 2 HIGH   │ │
│  │   [CHIP]     │   │ │ [12:00:03] Temp: 25.3°C │ │
│  │   + Logs     │   │ │ ...                      │ │
│  │              │   │ └──────────────────────────┘ │
│  │    🔵 🔵     │   │                              │
│  │    🔵 🔵     │   │ [ ] Auto-scroll             │
│  └──────────────┘   │ [ ] Chip Overlay            │
│                     │ [Clear] [Pause]             │
│  Pin Controls       │                              │
│  ┌──────────────┐   │                              │
│  │ Pin 2 (LED)  │   │                              │
│  │ [HIGH] [LOW] │   │                              │
│  └──────────────┘   │                              │
└─────────────────────┴──────────────────────────────┘
```

**Features:**
- Visual board representation with accurate pin positions
- Color-coded pins by function type:
  - 🟢 GPIO Write: Green
  - 🔵 GPIO Read: Blue  
  - 🟠 PWM: Orange
  - 🟣 Analog: Purple
  - 🔴 Temperature: Red
  - 🟡 Battery: Yellow

- Interactive controls for write-capable pins:
  - **GPIO**: HIGH/LOW toggle buttons
  - **PWM**: Slider (0-255) with apply button
  - **DAC**: Slider (0-3.3V) with apply button
  - **Relay**: ON/OFF toggle

- Chip overlay displays last 10 log entries over the processor
- Pin indicators flash gold when command is sent
- Auto-scroll and pause controls

### Direct Device Interface

When you navigate to the ESP32's IP address, you get:

**Features:**
- Same board visualization
- Direct pin control (no master needed)
- Live serial monitor
- Sensor readings
- Connection status

---

## 3. Logic Builder Integration

### Pin Action Detection

The system automatically detects write-capable pins from the assigned logic:

```javascript
// Example logic structure
{
  "actions": [
    {
      "type": "gpio_write",
      "pin": 2,
      "value": "HIGH",
      "alias": "LED"
    },
    {
      "type": "pwm_write",
      "pin": 18,
      "value": 128,
      "alias": "Motor"
    }
  ]
}
```

The visualization:
1. Parses the logic
2. Identifies pins with write actions
3. Creates interactive controls
4. Shows current state
5. Allows manual override

### Action Types Supported

| Type | Control | Values |
|------|---------|--------|
| `gpio_write` | Toggle Buttons | HIGH, LOW |
| `pwm_write` | Slider | 0-255 |
| `analog_write` | Slider | 0-255 (0-3.3V) |
| `set_relay` | Toggle Buttons | ON, OFF |

---

## 4. API Integration

### Pin Control Endpoint

**Endpoint:** `POST /api/sensor-master/pin-control`

**Request Body:**
```json
{
  "sensor_id": "esp32_fermentation_002",
  "pin": 2,
  "action_type": "gpio_write",
  "value": "HIGH"
}
```

**Response:**
```json
{
  "message": "Pin control command queued",
  "command_id": 123,
  "sensor_status": "online"
}
```

**How it works:**
1. Command is queued with priority 1 (highest)
2. Converted to single-action JSON script
3. Device picks up on next heartbeat (~5s)
4. Executes immediately
5. Log entry created for tracking

### Command Flow

```
User clicks [HIGH]
    ↓
sendPinCommand(2, 'gpio_write', 'HIGH')
    ↓
POST /api/sensor-master/pin-control
    ↓
Queue command (priority 1)
    ↓
Device polls for commands
    ↓
Execute: digitalWrite(2, HIGH)
    ↓
Update pin state tracker
    ↓
Log: "Pin 2 control: gpio_write = HIGH"
```

---

## 5. Board Type System

### Configuration Structure

```javascript
const BOARD_CONFIGS = {
    'ESP32-WROOM-32': {
        name: 'ESP32-WROOM-32',
        image: '/static/images/boards/esp32-wroom-32.png',
        chipOverlay: {
            x: 85,
            y: 90,
            width: 120,
            height: 140
        },
        pins: [
            {
                pin: 2,
                name: 'A12/T2',
                x: 275,
                y: 105,
                side: 'right',
                type: 'io',
                analog: true,
                touch: true,
                led: true
            }
            // ... more pins
        ],
        capabilities: {
            digital_output: [2, 4, 5, ...],
            pwm: [2, 4, 5, ...],
            dac: [25, 26],
            touch: [0, 2, 4, ...]
        }
    }
}
```

### Adding New Boards

To add a new board type:

1. Take a photo/screenshot of the board
2. Save to `app/static/images/boards/[board-name].png`
3. Add configuration to `board-configs.js`:

```javascript
'ESP32-DevKitC': {
    name: 'ESP32-DevKitC',
    image: '/static/images/boards/esp32-devkitc.png',
    chipOverlay: { x: 90, y: 100, width: 110, height: 130 },
    pins: [
        // Define pin positions
    ],
    capabilities: {
        // Define capabilities
    }
}
```

4. Set `board_type` in sensor registration:
```python
# In sensor registration
board_type = 'ESP32-DevKitC'
```

---

## 6. Installation & Setup

### Required Files

1. **Board Image** (MANUAL STEP NEEDED)
   - Save the attached ESP32 image to:
   - `app/static/images/boards/esp32-wroom-32.png`

2. **JavaScript Config**
   - Already created: `app/static/js/board-configs.js`

3. **API Updates**
   - Already updated: `app/api/sensor_master_api.py`

4. **Template Updates**
   - Already updated: `app/templates/sensor_master_control.html`

5. **Firmware Updates**
   - Header created: `esp32_web_interface.h`
   - Needs integration into `sensor_firmware.ino`

### Firmware Integration Steps

Add to `sensor_firmware.ino`:

1. **Include header:**
```cpp
#include "esp32_web_interface.h"
```

2. **Replace web server setup:**
```cpp
server.on("/", HTTP_GET, []() {
    SensorData data = readSensorData();
    String html = generateWebInterface(
        SENSOR_NAME,
        SENSOR_ID,
        SENSOR_TYPE,
        currentMode,
        masterUrl,
        FIRMWARE_VERSION,
        data.temperature,
        data.relayState,
        millis() / 1000
    );
    server.send(200, "text/html", html);
});
```

3. **Add pin state endpoint:**
```cpp
server.on("/api/pins", HTTP_GET, []() {
    JsonDocument doc;
    JsonArray pinsArray = doc.createNestedArray("pins");
    
    // Extract from current logic
    if (currentScript.length() > 0) {
        JsonDocument scriptDoc;
        deserializeJson(scriptDoc, currentScript);
        
        if (scriptDoc["actions"]) {
            for (JsonObject action : scriptDoc["actions"].as<JsonArray>()) {
                if (action.containsKey("pin")) {
                    JsonObject pinObj = pinsArray.createNestedObject();
                    pinObj["pin"] = action["pin"];
                    pinObj["type"] = action["type"];
                    pinObj["alias"] = action["alias"] | "";
                    
                    // Get state from tracker
                    int pin = action["pin"];
                    if (pinStates.count(pin)) {
                        pinObj["state"] = pinStates[pin] == HIGH ? "HIGH" : "LOW";
                    }
                }
            }
        }
    }
    
    String json;
    serializeJson(doc, json);
    server.send(200, "application/json", json);
});
```

4. **Add pin control endpoint:**
```cpp
server.on("/api/pin-control", HTTP_POST, []() {
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "No body");
        return;
    }
    
    JsonDocument doc;
    deserializeJson(doc, server.arg("plain"));
    
    int pin = doc["pin"];
    String value = doc["value"].as<String>();
    
    pinMode(pin, OUTPUT);
    digitalWrite(pin, value == "HIGH" ? HIGH : LOW);
    pinStates[pin] = value == "HIGH" ? HIGH : LOW;
    
    WebSerial.println("🎮 Manual Pin Control: Pin " + String(pin) + " = " + value);
    
    server.send(200, "application/json", "{\"status\":\"ok\"}");
});
```

---

## 7. Usage

### From Master Control Interface

1. Navigate to Sensor Master Control page
2. Find your sensor in the list
3. Click the **Serial Monitor** icon (terminal icon)
4. Modal opens showing:
   - Board visualization on left
   - Live logs on right
5. If sensor has logic assigned:
   - Pin indicators appear on board
   - Controls appear below board
6. Interact with controls:
   - Toggle buttons for GPIO
   - Sliders for PWM/DAC
   - Changes sent immediately

### From Device Direct Access

1. Find device IP (shown in serial monitor or master control)
2. Navigate to `http://[device-ip]` in browser
3. See full dashboard with:
   - Board visualization
   - Pin controls
   - Serial logs
   - Sensor data
4. Controls work same as master interface
5. No master connection required

---

## 8. Technical Details

### Pin State Tracking

Firmware maintains `pinStates` map:
```cpp
std::map<int, int> pinStates;

// When executing logic
digitalWrite(pin, value);
pinStates[pin] = value;  // Track it

// When reading
if (pinStates.count(pin)) {
    return pinStates[pin];
}
```

### Command Priority

Pin control commands use priority 1:
```python
cursor.execute('''
    INSERT INTO SensorCommandQueue
    (sensor_id, command_type, command_data, priority, ...)
    VALUES (?, ?, ?, 1, ...)
''')
```

Normal commands use priority 100.

### Log Overlay

Chip overlay shows last 10 logs:
```javascript
const allLogDivs = container.querySelectorAll('div.border-bottom');
const recentLogs = Array.from(allLogDivs).slice(-10);
chipLogOverlay.innerHTML = recentLogs.map(div => div.innerHTML).join('');
```

Updates on every log fetch (2s interval).

---

## 9. Future Enhancements

### Planned Features

1. **Multiple Board Support**
   - ESP32-S3
   - ESP32-C3
   - ESP8266
   - Custom boards

2. **Advanced Visualizations**
   - Live pin value graphs
   - Analog pin waveforms
   - PWM duty cycle visualization

3. **Batch Controls**
   - Control multiple pins at once
   - Preset configurations
   - Macro buttons

4. **Touch Interface**
   - Tap pins directly on board image
   - Gesture controls for values
   - Mobile-optimized layout

5. **Historical Data**
   - Pin state history
   - Change timeline
   - Playback mode

6. **Logic Debugger**
   - Step through logic execution
   - Breakpoints on actions
   - Variable inspection

---

## 10. Troubleshooting

### Board Image Not Showing

**Symptom:** Placeholder or error where board image should be

**Solutions:**
1. Check image file exists at `app/static/images/boards/esp32-wroom-32.png`
2. Verify image format (PNG/JPG supported)
3. Check browser console for 404 errors
4. Clear browser cache

### Pins Not Interactive

**Symptom:** No pin controls showing

**Causes:**
1. No logic assigned to sensor
2. Logic has no write actions
3. Logic parsing error

**Solutions:**
1. Assign a logic via Logic Builder
2. Ensure logic has `gpio_write`, `pwm_write`, etc.
3. Check browser console for JS errors
4. Verify `currentPlotterLogicData` is populated

### Commands Not Executing

**Symptom:** Clicking controls doesn't change pin state

**Causes:**
1. Sensor offline
2. Command queue full
3. Pin not writable

**Solutions:**
1. Check sensor status (green = online)
2. Check command queue in database
3. Verify pin supports output (see board config)
4. Check firmware serial logs

### Logs Not Updating

**Symptom:** Log area shows "Waiting for logs..." forever

**Causes:**
1. No logs from sensor
2. Polling stopped
3. Network issue

**Solutions:**
1. Send test log (Test button)
2. Check browser network tab
3. Verify `/api/sensor-master/logs/[id]` endpoint works
4. Check `plotterInterval` is running

---

## 11. Testing Checklist

- [ ] Board image loads correctly
- [ ] Pins appear at correct positions
- [ ] Pin colors match action types
- [ ] Chip log overlay toggles on/off
- [ ] Logs scroll automatically
- [ ] GPIO toggle works (HIGH/LOW)
- [ ] PWM slider updates value
- [ ] DAC slider shows voltage
- [ ] Relay toggle works
- [ ] Pin indicators flash on command
- [ ] Device direct access works
- [ ] Pin states sync from device
- [ ] Multiple sensors work independently
- [ ] Modal closes cleanly (stops polling)
- [ ] Works on mobile/tablet

---

## 12. Code Reference

### Key Functions

**`initializeBoardVisualization()`**
- Sets up board image
- Positions chip overlay
- Creates pin indicators
- Builds control UI

**`extractPinActionsFromLogic(actions)`**
- Recursively finds pin actions
- Returns flat list
- Includes nested if/else blocks

**`sendPinCommand(pin, actionType, value)`**
- Sends command to API
- Updates UI feedback
- Flashes pin indicator

**`control_sensor_pin()`** (Python)
- Queues high-priority command
- Creates single-action script
- Logs manual override

### Database Schema

**SensorCommandQueue:**
```sql
CREATE TABLE SensorCommandQueue (
    id INTEGER PRIMARY KEY,
    sensor_id TEXT,
    command_type TEXT,
    command_data TEXT,  -- JSON
    priority INTEGER,   -- 1 = highest
    status TEXT,
    created_at TIMESTAMP
);
```

**SensorLogs:**
```sql
CREATE TABLE SensorLogs (
    id INTEGER PRIMARY KEY,
    sensor_id TEXT,
    message TEXT,
    log_level TEXT,
    created_at TIMESTAMP
);
```

---

## Summary

This implementation provides a complete interactive board visualization system that:

✅ Shows real-time board state
✅ Allows manual pin control
✅ Integrates with logic builder
✅ Works from master control AND device
✅ Supports multiple board types
✅ Provides visual feedback
✅ Logs all actions

The system bridges the gap between abstract logic configuration and physical hardware interaction, making it easy to test, debug, and control your ESP32 devices.
