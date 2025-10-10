# Sensor Type Validation Fix

## Problem
WiFi Signal data was being recorded to Sample Bottle entries even though Sample Bottles only had Temperature enabled as a sensor type. The system was not validating that sensor types matched the entry type's `enabled_sensor_types` configuration before recording data.

## Root Cause
Three areas were not enforcing sensor type validation:

1. **Device Scheduler (`_store_default_esp32_data`)**: Recorded all available sensor data (Temperature, WiFi Signal, etc.) to ALL linked entries without checking if each entry type supported those sensor types.

2. **Device Scheduler (`_store_esp32_fermentation_data`)**: When using sensor mappings, it didn't validate that the mapped sensor type was enabled for each target entry.

3. **Shared Sensor Service**: Only logged warnings when sensor types didn't match but still allowed the data to be stored.

4. **Manual API Endpoint**: Didn't validate sensor types when manually adding sensor data.

## Solution Implemented

### 1. Device Scheduler - Default ESP32 Data (`app/device_scheduler.py`)
- Added logic to fetch `enabled_sensor_types` for each entry before recording
- Added validation checks for each sensor type before inserting:
  - `Temperature` - only records if enabled
  - `Target Temperature` - only records if enabled
  - `Heating Status` - only records if enabled
  - `WiFi Signal` - **only records if enabled** (fixes the main issue)
  - `Free Memory` - only records if enabled
  - `Device Status` - only records if enabled

### 2. Device Scheduler - Mapped Sensor Data (`app/device_scheduler.py`)
- Added logic to fetch `enabled_sensor_types` for each entry
- Added validation before recording each mapped sensor reading
- Now skips sensor types that aren't enabled for the target entry

### 3. Shared Sensor Service (`app/services/shared_sensor_service.py`)
- Changed from warning-only to actual filtering
- Now removes entries from the list if they don't support the sensor type
- Raises an error if no valid entries remain after filtering
- Only creates sensor data for entries that actually support the sensor type

### 4. Manual API Endpoint (`app/api/entry_api.py`)
- Added validation to check entry's `enabled_sensor_types` before accepting manual sensor data
- Returns a 400 error with clear message if sensor type is not enabled
- Includes list of enabled types in error response

## Expected Behavior After Fix

### Fermentation Chamber (Temperature + WiFi Signal enabled)
✅ Records Temperature data  
✅ Records WiFi Signal data  
❌ Won't record other sensor types not in enabled list

### Sample Bottle (Temperature only enabled)
✅ Records Temperature data  
❌ Won't record WiFi Signal data  
❌ Won't record other sensor types not in enabled list

## Testing the Fix

1. **Restart the application** to reload the device scheduler with the new validation logic
2. **Wait for next device poll cycle** (default: 30 seconds)
3. **Check sensor data** for Sample Bottle entries - should no longer show WiFi Signal data
4. **Check sensor data** for Fermentation Chamber entries - should continue to show both Temperature and WiFi Signal

## Manual Testing Commands

```python
# Check current sensor data for an entry
from app.db import get_connection
conn = get_connection()
cursor = conn.cursor()

# Get recent sensor data for a specific entry
cursor.execute('''
    SELECT sensor_type, value, recorded_at 
    FROM SensorData 
    WHERE entry_id = ? 
    ORDER BY recorded_at DESC 
    LIMIT 20
''', (ENTRY_ID,))

for row in cursor.fetchall():
    print(f"{row['recorded_at']}: {row['sensor_type']} = {row['value']}")
```

## Files Modified

1. `/app/device_scheduler.py` - Device polling and data recording
2. `/app/services/shared_sensor_service.py` - Shared sensor data validation
3. `/app/api/entry_api.py` - Manual sensor data API endpoint validation

## Benefits

- **Data Integrity**: Only valid sensor types are recorded for each entry
- **Cleaner Data**: No more irrelevant sensor data cluttering entry views
- **Better Performance**: Reduces unnecessary data storage and processing
- **Clear Errors**: Users get helpful error messages when trying to add invalid sensor types
- **Flexible Configuration**: Entry types can have different sensor configurations without data leakage
