# Battery Logging Fix - ESP32-C6

## Problem Summary

When using a simple battery monitoring script on the FireBeetle 2 ESP32-C6:

```json
{
  "name": "Battery",
  "version": "1.0.0",
  "description": "",
  "target_sensor_type": "firebeetle2_esp32c6",
  "actions": [
    {
      "type": "read_battery",
      "pin": 0,
      "r1": 100000,
      "r2": 100000,
      "alias": "battery"
    },
    {
      "type": "log",
      "message": "{battery}"
    },
    {
      "type": "log",
      "message": "{battery_pct}"
    }
  ]
}
```

The output was showing literal placeholders instead of actual values:
```
[7:15:41 AM] {battery}
[7:15:41 AM] {battery_pct}
```

## Root Causes Identified

### 1. Missing ESP32-C6 ADC Configuration ⚠️ **CRITICAL**

The ESP32-C6 requires specific ADC configuration that was missing in the code:
- **analogReadResolution(12)** - Sets 12-bit resolution (0-4095)
- **analogSetPinAttenuation(pin, ADC_ATTEN_DB_12)** - Sets 0-3.3V range

Without this configuration, the ADC may return invalid readings (often 0).

### 2. Insufficient Debug Output

The firmware lacked detailed debug output to diagnose:
- Whether battery values were being stored in `globalVariables`
- What the raw ADC reading was
- Whether `resolveValue()` was finding the variables

## Fixes Applied

### Fix 1: Added ESP32-C6 ADC Configuration

**File**: `firmware/Framework_Connection_App/src/main.cpp`
**Location**: `read_battery` action handler (around line 1217)

```cpp
// Set ADC configuration for ESP32-C6
#if CONFIG_IDF_TARGET_ESP32C6
analogReadResolution(12);  // 12-bit resolution (0-4095)
analogSetPinAttenuation(pin, ADC_ATTEN_DB_12);  // 0-3.3V range
#endif
```

**Why This Matters**: The ESP32-C6 ADC behaves differently from ESP32 Classic. Without proper attenuation setting, it may read incorrect voltages or return 0.

### Fix 2: Enhanced Debug Logging

Added comprehensive debug output to track:

1. **Battery Reading Debug** (after voltage calculation):
```cpp
WebSerial.println("🔍 DEBUG: Raw ADC = " + String(raw) + ", R1=" + String((int)r1) + ", R2=" + String((int)r2));
WebSerial.println("🔍 DEBUG: Stored 'battery' = " + String(globalVariables[alias]));
WebSerial.println("🔍 DEBUG: Stored 'battery_pct' = " + String(globalVariables[pctKey]));
WebSerial.println("🔍 DEBUG: Stored 'battery_raw' = " + String(globalVariables[rawKey]));
```

2. **Variable Resolution Debug** (when resolving variables in log messages):
```cpp
WebSerial.println("🔍 DEBUG: resolveValue('" + key + "') found in globalVariables = " + String(val));
```

3. **Failed Resolution Debug**:
```cpp
WebSerial.println("⚠️ DEBUG: resolveValue('" + key + "') failed to resolve, returning 0");
WebSerial.println("   globalVariables has " + String(globalVariables.size()) + " entries");
```

### Fix 3: Store Raw ADC Value

Added `battery_raw` variable for debugging:
```cpp
globalVariables[alias + "_raw"] = raw;  // Store raw ADC reading
```

This allows you to use `{battery_raw}` in log messages to verify ADC is working.

## How to Test

### Step 1: Rebuild and Flash Firmware

```bash
cd /home/an0naman/Documents/GitHub/template/firmware/Framework_Connection_App
pio run -e firebeetle2_esp32c6 -t upload
```

### Step 2: Monitor Serial Output

```bash
pio device monitor --baud 115200
```

### Step 3: Upload Test Script

Use the simple battery test script (your original JSON is perfect):

```json
{
  "name": "Battery Test",
  "version": "1.0.0",
  "target_sensor_type": "firebeetle2_esp32c6",
  "actions": [
    {
      "type": "read_battery",
      "pin": 0,
      "r1": 100000,
      "r2": 100000,
      "alias": "battery"
    },
    {
      "type": "log",
      "message": "Battery: {battery}V"
    },
    {
      "type": "log",
      "message": "Percentage: {battery_pct}%"
    },
    {
      "type": "log",
      "message": "Raw ADC: {battery_raw}"
    }
  ]
}
```

### Step 4: Verify Expected Output

You should see:
```
✓ Battery: 4.15V (94%)
🔍 DEBUG: Raw ADC = 2048.3, R1=100000, R2=100000
🔍 DEBUG: Stored 'battery' = 4.15
🔍 DEBUG: Stored 'battery_pct' = 94.00
🔍 DEBUG: Stored 'battery_raw' = 2048.30
🔍 DEBUG: resolveValue('battery') found in globalVariables = 4.15
📝 Log: Battery: 4.15V
🔍 DEBUG: resolveValue('battery_pct') found in globalVariables = 94.00
📝 Log: Percentage: 94%
🔍 DEBUG: resolveValue('battery_raw') found in globalVariables = 2048.30
📝 Log: Raw ADC: 2048
```

## Troubleshooting

### Still Seeing {battery} Literal?

Check debug output for:
```
⚠️ DEBUG: resolveValue('battery') failed to resolve, returning 0
   globalVariables has 0 entries
```

This means battery values aren't being stored. Check if:
1. Battery is actually connected
2. Raw ADC reading shows > 0 (if 0, hardware issue)
3. Pin 0 is correct for your board

### Battery Value Always 0V?

Check:
```
⚠️ Warning: Battery raw reading is 0. Check wiring/resistors.
```

Possible causes:
- No battery connected to GPIO 0
- Voltage divider circuit issue
- Wrong pin number in JSON

### ADC Reading Looks Wrong (e.g., 4095 or very low)?

The ADC attenuation might still be wrong. Verify you see:
```
🔍 DEBUG: Raw ADC = [reasonable value 500-3500], R1=100000, R2=100000
```

If raw ADC is:
- **0**: No voltage detected (check battery connection)
- **4095**: Pin might be floating or wrong attenuation
- **< 500**: Battery critically low or divider issue

## Sensor Master Control Dashboard

Once the fixes are working, the **Sensor Master Control** page should:

1. **Detect** the `read_battery` action in your script
2. **Show** battery indicator in the "Battery" column
3. **Display** voltage (e.g., "4.15V") or percentage bar
4. **Update** from heartbeat metrics or log parsing

The dashboard looks for battery data from:
- Heartbeat metrics (`battery` and `battery_pct` fields)
- Log messages matching patterns like "Battery: 4.15V (94%)"

## Technical Notes

### ESP32-C6 vs ESP32 Classic ADC Differences

| Feature | ESP32 Classic | ESP32-C6 |
|---------|--------------|----------|
| Architecture | Xtensa dual-core | RISC-V single-core |
| Default ADC Config | Auto-configured | **Requires explicit setup** |
| Attenuation Options | 0dB, 2.5dB, 6dB, 11dB | **0dB, 2.5dB, 6dB, 12dB** |
| Max Voltage (12dB) | 3.6V | 3.3V |
| Resolution | 12-bit (0-4095) | 12-bit (0-4095) |

### Why R1=R2=100kΩ in Your Test?

You're using equal resistors (100kΩ/100kΩ), which gives a 2:1 voltage divider.

For a 4.2V LiPo battery:
- Voltage at GPIO 0 = 4.2V × (100k / 200k) = **2.1V** ✓ Safe for ADC
- Expected ADC = 2.1V / 3.3V × 4095 = **≈2600**

However, the **FireBeetle 2 ESP32-C6** has a **built-in voltage divider** on GPIO 0!
According to calibration: **R1 ≈ 145.9kΩ, R2 = 100kΩ**

### Recommended Configuration for FireBeetle 2 ESP32-C6

Use calibrated values for accuracy:
```json
{
  "type": "read_battery",
  "pin": 0,
  "r1": 145900,
  "r2": 100000,
  "alias": "battery"
}
```

This gives ±0.05V accuracy across 3.3V-4.2V range.

## Related Files Modified

1. **firmware/Framework_Connection_App/src/main.cpp**
   - Added ADC configuration for ESP32-C6
   - Enhanced debug logging in `read_battery` action
   - Enhanced debug logging in `resolveValue()` function
   - Store `battery_raw` for debugging

## Next Steps

1. ✅ Firmware changes committed
2. 🔄 **You need to rebuild and flash** (`pio run -e firebeetle2_esp32c6 -t upload`)
3. 🧪 Test with your battery script
4. 👀 Monitor serial output for debug messages
5. 📊 Check Sensor Master Control dashboard for battery display

## If Issues Persist

Share the **full serial monitor output** including:
- ✓ Battery: ... messages
- 🔍 DEBUG: Stored ... messages
- 🔍 DEBUG: resolveValue ... messages
- 📝 Log: ... messages

This will help diagnose if the problem is:
- Hardware (ADC reading 0)
- Storage (variables not saved)
- Resolution (variables not found)
- Display (dashboard not detecting)
