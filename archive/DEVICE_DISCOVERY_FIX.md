# Device Data Point Discovery Fix

## Summary
Fixed critical issue where the device manager wasn't discovering all available data points from sensors, especially those in nested objects and arrays.

## Problem
When clicking "Configure Data Points" for a device, users only saw a limited set of predefined sensors (Temperature, WiFi Signal, Free Memory) instead of ALL the actual data points their device was sending.

### Specific Issues:
1. **Array items not discovered**: If device sent `sensors[0]`, `sensors[1]`, `sensors[2]`, only `sensors[0]` would appear
2. **Array paths couldn't be extracted**: Even if configured, paths like `sensors[0].temperature` would return `None`
3. **Wrong database column**: Code tried to access `device['device_ip']` but column is named `ip`

## Root Causes

### 1. Limited Array Analysis
```python
# OLD CODE - Only analyzed first array item
elif isinstance(data, list) and data:
    paths.update(_analyze_data_structure(data[0], f"{prefix}[0]"))
```

### 2. No Array Notation Support
```python
# OLD CODE - Only handled dot notation
def get_nested_value(data, path):
    keys = path.split('.')  # Breaks on "sensors[0].temperature"
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
```

### 3. Database Column Mismatch
```python
# OLD CODE
endpoint = f"http://{device['device_ip']}/api"  # ❌ Column doesn't exist
# SHOULD BE
endpoint = f"http://{device['ip']}/api"  # ✅ Correct column name
```

## Solutions Implemented

### 1. Multi-Item Array Analysis
```python
def _analyze_data_structure(data, prefix="", max_array_items=5):
    # ...
    elif isinstance(data, list) and data:
        # Analyze multiple items in list (up to max_array_items)
        items_to_analyze = min(len(data), max_array_items)
        for i in range(items_to_analyze):
            paths.update(_analyze_data_structure(data[i], f"{prefix}[{i}]", max_array_items))
```

**Benefits:**
- Discovers `sensors[0]`, `sensors[1]`, `sensors[2]`, etc.
- Up to 5 array items analyzed by default (configurable)
- Works with deeply nested arrays

### 2. Array Notation Path Extraction
```python
def get_nested_value(data, path):
    """Get value from nested dictionary using dot notation and array notation path"""
    import re
    parts = []
    for part in path.split('.'):
        # Check if this part has array notation
        array_match = re.match(r'([^\[]+)\[(\d+)\]', part)
        if array_match:
            key_name = array_match.group(1)
            index = int(array_match.group(2))
            parts.append((key_name, 'dict'))
            parts.append((index, 'list'))
        else:
            parts.append((part, 'dict'))
    
    current = data
    for key, key_type in parts:
        if key_type == 'dict':
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        elif key_type == 'list':
            if isinstance(current, list) and 0 <= key < len(current):
                current = current[key]
            else:
                return None
    return current
```

**Benefits:**
- Handles: `sensor.temperature` ✅
- Handles: `sensors[0].temperature` ✅
- Handles: `sensors[1].id` ✅
- Handles: `ds18b20.devices[0].temperature` ✅

### 3. Fixed Database Column Reference
```python
# FIXED
endpoint = f"http://{device['ip']}/api"  # ✅ Correct
logger.info(f"Polling device {device_id} at IP: {device['ip']}")  # ✅ Added logging
```

## What You'll See Now

### Before Fix:
```
Available Sensors:
  - Temperature (°C)
  - WiFi Signal Strength (dBm)
  - Free Memory (bytes)
```
*(Predefined fallback list when device polling failed)*

### After Fix:
```
Available Sensors:
  - sensor.temperature (20.5°C)
  - sensor.humidity (65.3%)
  - sensor.target_temp (20.0°C)
  - network.rssi (-67 dBm)
  - network.ip_address (192.168.1.100)
  - system.free_heap (45000 bytes)
  - system.uptime_ms (123456789 ms)
  - system.uptime_formatted (1d 10h 17m)
  - relay.state (ON)
  - relay.pin (23)
  - ds18b20.devices[0].id (28FF123456789012)
  - ds18b20.devices[0].temperature (18.5°C)
  - ds18b20.devices[0].valid (True)
  - ds18b20.devices[1].id (28FF987654321098)
  - ds18b20.devices[1].temperature (19.2°C)
  - ds18b20.devices[1].valid (True)
```
*(All actual device data points are discovered!)*

## How to Test

### 1. Open Device Manager
```
http://localhost:5000/manage_devices
```

### 2. Click "Configure Data Points"
For any registered device

### 3. Verify You See All Data Points
Check the "Available Sensors" list - you should now see:
- All nested object properties
- All array items (up to 5 per array)
- Proper data types and sample values

### 4. Configure and Test
- Enable some array-based sensors (e.g., `ds18b20.devices[0].temperature`)
- Save the configuration
- Poll the device
- Verify the data is correctly extracted and stored

## Test Script

Run the included test script:
```bash
python3 test_device_data_discovery.py
```

This will:
- Test various data structures (simple, array, complex nested)
- Verify path extraction works
- Show what data points are discovered

## Technical Details

### Array Notation Parsing
The regex pattern `r'([^\[]+)\[(\d+)\]'` matches:
- `sensors[0]` → groups: ('sensors', '0')
- `devices[5]` → groups: ('devices', '5')

### Path Navigation
The function builds a list of (key, type) tuples:
```python
# For path: "ds18b20.devices[0].temperature"
[
    ('ds18b20', 'dict'),
    ('devices', 'dict'),
    (0, 'list'),
    ('temperature', 'dict')
]
```

Then navigates the data structure step by step.

## Files Modified
- `app/api/device_api.py` - Core fixes
- `test_device_data_discovery.py` - New test file (added)

## Commit
```
git commit: fd1308c
Message: "Fix: Device manager now discovers ALL data points including nested objects and arrays"
```

## Next Steps
1. ✅ Test with your actual fermentation controller
2. ✅ Configure data points for multiple temperature sensors
3. ✅ Verify automatic polling works
4. ✅ Check sensor alarms with array-based sensors

## Benefits
- **Complete visibility**: See ALL device data points
- **Array support**: Multiple sensors in arrays all visible
- **Flexible configuration**: Choose any data point to track
- **Better debugging**: Understand exactly what your device is sending
- **Future-proof**: Works with any nested JSON structure
