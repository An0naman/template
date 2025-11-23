# JSON Script Commands Reference

## Overview

The ESP32 Sensor Master Control system uses **JSON-based command scripts** instead of raw C++ code. This is because **ESP32 devices cannot compile C++ code at runtime**. Instead, the firmware includes a JSON interpreter that executes pre-defined actions.

## Why JSON Commands?

✅ **Runtime Execution**: No compilation needed, scripts execute immediately  
✅ **Safe**: Only pre-defined actions can be executed  
✅ **Simple**: Easy to generate, validate, and debug  
✅ **Portable**: Same format works across different sensor types  
✅ **Updateable**: Change behavior without re-flashing firmware  

## Script Format

```json
{
  "name": "Script Name",
  "version": "1.0.0",
  "description": "What this script does",
  "actions": [
    {"type": "action_type", "param1": "value1"},
    {"type": "another_action", "param2": "value2"}
  ]
}
```

## Available Commands

### 1. GPIO Write

Set a digital pin HIGH or LOW.

```json
{"type": "gpio_write", "pin": 2, "value": "HIGH"}
{"type": "gpio_write", "pin": 2, "value": "LOW"}
```

**Parameters:**
- `pin` (int): GPIO pin number (e.g., 2, 15, 16)
- `value` (string): "HIGH" or "LOW"

**Example - Blink LED:**
```json
{
  "name": "LED Blink",
  "version": "1.0.0",
  "actions": [
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 1000},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 1000}
  ]
}
```

---

### 2. GPIO Read

Read the state of a digital input pin.

```json
{"type": "gpio_read", "pin": 15}
```

**Parameters:**
- `pin` (int): GPIO pin number to read

**Output:** Prints pin value (0 or 1) to serial monitor

---

### 3. Analog Read

Read an analog value from an ADC pin (0-4095 on ESP32).

```json
{"type": "analog_read", "pin": 34}
```

**Parameters:**
- `pin` (int): ADC pin number (typically 32-39 on ESP32)

**Output:** Prints ADC value (0-4095) to serial monitor

**Example - Read Potentiometer:**
```json
{
  "name": "Read Potentiometer",
  "version": "1.0.0",
  "actions": [
    {"type": "analog_read", "pin": 34},
    {"type": "delay", "ms": 500}
  ]
}
```

---

### 4. Read Temperature

Read temperature from configured sensor (calls `readSensorData()`).

```json
{"type": "read_temperature"}
```

**Parameters:** None

**Output:** Prints temperature in Celsius to serial monitor

**Example - Temperature Monitor:**
```json
{
  "name": "Temperature Monitor",
  "version": "1.0.0",
  "actions": [
    {"type": "read_temperature"},
    {"type": "log", "message": "Temperature check complete"},
    {"type": "delay", "ms": 5000}
  ]
}
```

---

### 5. Set Relay

Control a relay (implement hardware-specific logic in firmware).

```json
{"type": "set_relay", "state": true}
{"type": "set_relay", "state": false}
```

**Parameters:**
- `state` (boolean): `true` for ON, `false` for OFF

**Example - Relay Cycle:**
```json
{
  "name": "Relay Test",
  "version": "1.0.0",
  "actions": [
    {"type": "set_relay", "state": true},
    {"type": "delay", "ms": 5000},
    {"type": "set_relay", "state": false},
    {"type": "delay", "ms": 1000}
  ]
}
```

---

### 6. Delay

Pause execution for specified milliseconds.

```json
{"type": "delay", "ms": 1000}
```

**Parameters:**
- `ms` (int): Delay duration in milliseconds

**Note:** Use delays between actions to control timing

---

### 7. Log

Print a message to the serial monitor.

```json
{"type": "log", "message": "Hello from script!"}
```

**Parameters:**
- `message` (string): Text to print

**Example - Debug Script:**
```json
{
  "name": "Debug Test",
  "version": "1.0.0",
  "actions": [
    {"type": "log", "message": "Starting test sequence"},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "log", "message": "LED turned ON"},
    {"type": "delay", "ms": 1000},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "log", "message": "LED turned OFF"}
  ]
}
```

---

## Complete Examples

### Example 1: SOS Morse Code

```json
{
  "name": "SOS Pattern",
  "version": "1.0.0",
  "description": "SOS morse code on LED (... --- ...)",
  "actions": [
    {"type": "log", "message": "Starting SOS pattern"},
    
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 600},
    
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 600},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 600},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 600},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 600},
    
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 200},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 2000},
    
    {"type": "log", "message": "SOS pattern complete"}
  ]
}
```

### Example 2: Multi-Sensor Reading

```json
{
  "name": "Sensor Scan",
  "version": "1.0.0",
  "description": "Read all sensors and log data",
  "actions": [
    {"type": "log", "message": "Starting sensor scan"},
    
    {"type": "read_temperature"},
    {"type": "delay", "ms": 100},
    
    {"type": "gpio_read", "pin": 15},
    {"type": "delay", "ms": 100},
    
    {"type": "analog_read", "pin": 34},
    {"type": "delay", "ms": 100},
    
    {"type": "log", "message": "Sensor scan complete"}
  ]
}
```

### Example 3: Temperature-Based Relay Control

```json
{
  "name": "Temperature Control",
  "version": "1.0.0",
  "description": "Turn relay on based on temperature",
  "actions": [
    {"type": "read_temperature"},
    {"type": "log", "message": "Checking temperature threshold"},
    
    {"type": "set_relay", "state": true},
    {"type": "delay", "ms": 10000},
    
    {"type": "set_relay", "state": false},
    {"type": "log", "message": "Temperature control cycle complete"}
  ]
}
```

### Example 4: Triple Blink Pattern

```json
{
  "name": "Triple Blink",
  "version": "1.0.0",
  "description": "Fast triple blink pattern",
  "actions": [
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 150},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 150},
    
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 150},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 150},
    
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 150},
    {"type": "gpio_write", "pin": 2, "value": "LOW"},
    {"type": "delay", "ms": 2000}
  ]
}
```

---

## Uploading Scripts

### Via Web UI

1. Navigate to **Sensor Master Control** page
2. Click **"Upload Script"** button
3. Select your sensor from dropdown
4. Paste your JSON script
5. Set version and description
6. Click **"Upload to Sensor"**

### Via API

```bash
curl -X POST http://localhost:5001/api/sensor-master/script \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "esp32_fermentation_001",
    "script_content": "{\"actions\":[{\"type\":\"gpio_write\",\"pin\":2,\"value\":\"HIGH\"}]}",
    "script_version": "1.0.0",
    "script_type": "json",
    "description": "LED control"
  }'
```

---

## How It Works

1. **Upload**: JSON script saved to database
2. **Poll**: ESP32 checks for updates every 30 seconds
3. **Download**: ESP32 downloads new script via HTTP GET
4. **Parse**: ArduinoJson library parses JSON
5. **Execute**: Each action executes sequentially
6. **Report**: ESP32 reports execution back to master

---

## Limitations

⚠️ **No Loops**: Scripts execute once, use the dashboard to trigger repeatedly  
⚠️ **No Conditionals**: Use multiple scripts for different conditions  
⚠️ **Fixed Actions**: Only pre-defined actions available (extensible in firmware)  
⚠️ **Size Limit**: Keep scripts under 2KB for reliable parsing  

---

## Extending Commands

To add new commands, modify the `executeLocalScript()` function in your ESP32 firmware:

```cpp
} else if (type == "pwm_write") {
  // Custom PWM command
  int pin = action["pin"] | 2;
  int dutyCycle = action["duty"] | 128;
  ledcWrite(0, dutyCycle);
  Serial.println("  ✓ PWM Write: Pin " + String(pin) + " = " + String(dutyCycle));
}
```

---

## Best Practices

✅ **Use Descriptive Names**: Help identify scripts later  
✅ **Version Everything**: Track changes with semantic versioning  
✅ **Add Logs**: Include log messages for debugging  
✅ **Test Small**: Start with simple 2-3 action scripts  
✅ **Document**: Use descriptions to explain script purpose  
✅ **Mind Timing**: Use appropriate delays between actions  

---

## Troubleshooting

### Script Not Executing

- Check ESP32 is in ONLINE mode
- Verify script was uploaded successfully
- Check serial monitor for parse errors
- Ensure JSON is valid (use jsonlint.com)

### Parse Errors

- Use double quotes for JSON strings
- Escape special characters properly
- Keep scripts under 2KB
- Validate JSON before uploading

### Actions Not Working

- Verify pin numbers match your hardware
- Check connections (LED, relays, sensors)
- Review serial monitor output
- Test individual actions first

---

## Need More?

If you need more complex behavior:
- Create multiple scripts for different scenarios
- Use configuration templates for parameters
- Implement custom actions in firmware
- Consider MicroPython for full programmability
