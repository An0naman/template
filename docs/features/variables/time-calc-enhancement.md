# Time Calc Enhancement: Intuitive Value B Units

## Overview

Enhanced the `time_calc` block to make **Value B** more intuitive when using the "add" operation. Instead of requiring manual conversion to seconds, users can now enter duration values in their preferred unit (minutes, hours, days) and the system automatically converts them.

## What Changed

### Before ❌
```json
{
  "type": "time_calc",
  "result_var": "NextCheck",
  "time_op": "add",
  "value_a": "CurrentTime",
  "value_b": "600",          // Had to manually calculate: 10 minutes = 600 seconds
  "output_unit": "seconds"
}
```

### After ✅
```json
{
  "type": "time_calc",
  "result_var": "NextCheck",
  "time_op": "add",
  "value_a": "CurrentTime",
  "value_b": "600",           // Automatically converted from 10 minutes
  "value_b_raw": "10",        // Original user input
  "value_b_unit": "minutes",  // Unit selector
  "output_unit": "seconds"
}
```

## Features

### 1. Unit Selector for "Add" Operations

When `time_op` is set to `add`, a new **Value B Unit** dropdown appears with options:
- **Seconds** (default)
- **Minutes** 
- **Hours**
- **Days**
- **Raw** (no conversion - for variables already in seconds)

### 2. Automatic Conversion

The system automatically converts the entered value to seconds based on the selected unit:

| Unit     | Conversion Factor |
|----------|-------------------|
| Seconds  | ×1                |
| Minutes  | ×60               |
| Hours    | ×3600             |
| Days     | ×86400            |
| Raw      | No conversion     |

### 3. Visual Feedback

The UI shows the converted value in real-time:
```
Value B (Duration to Add)
[10                     ]
✨ Enter a number or variable. Will use: 600 seconds
```

### 4. Variable Support

When entering a variable name (e.g., `myDuration`), set the unit to **"Raw"** to use the variable's value without conversion.

## Use Cases

### Example 1: Schedule Next Weather Check in 10 Minutes
```json
{
  "type": "time_calc",
  "result_var": "NextWeatherCheck",
  "time_op": "add",
  "value_a": "CurrentTime",
  "value_b": "600",
  "value_b_raw": "10",
  "value_b_unit": "minutes",
  "output_unit": "seconds"
}
```

**User enters:** `10` in Value B, selects `minutes` from dropdown  
**System converts to:** `600` seconds automatically  

### Example 2: Hibernate for 2 Hours
```json
{
  "type": "time_calc",
  "result_var": "WakeTime",
  "time_op": "add",
  "value_a": "CurrentTime",
  "value_b": "7200",
  "value_b_raw": "2",
  "value_b_unit": "hours",
  "output_unit": "seconds"
}
```

**User enters:** `2` in Value B, selects `hours` from dropdown  
**System converts to:** `7200` seconds automatically  

### Example 3: Using a Variable Duration
```json
{
  "type": "variable_op",
  "name": "delayDuration",
  "operation": "=",
  "value": "1800"
},
{
  "type": "time_calc",
  "result_var": "NextRun",
  "time_op": "add",
  "value_a": "CurrentTime",
  "value_b": "delayDuration",
  "value_b_raw": "delayDuration",
  "value_b_unit": "raw",
  "output_unit": "seconds"
}
```

**User enters:** `delayDuration` in Value B, selects `raw` from dropdown  
**System uses:** Variable value as-is (1800 seconds)  

### Example 4: Diff Operation (No Change)

For `diff` operations, Value B works as before - no unit selector needed:
```json
{
  "type": "time_calc",
  "result_var": "TimeRemaining",
  "time_op": "diff",
  "value_a": "FutureTimestamp",
  "value_b": "CurrentTime",
  "output_unit": "minutes"
}
```

## UI Changes

### New Fields (for "add" operations only)

1. **Value B Unit Dropdown**
   - Location: Appears next to Value B input when `time_op = "add"`
   - Options: seconds, minutes, hours, days, raw
   - Default: seconds

2. **Dynamic Placeholder**
   - "add" operation: `"e.g. 10 (see unit selector →)"`
   - "diff" operation: `"Variable name or timestamp"`

3. **Smart Help Text**
   - Shows converted value in real-time
   - Context-aware based on operation type

4. **Dynamic Examples**
   - Operation-specific examples in the info box
   - Shows conversion examples for "add"
   - Shows timestamp examples for "diff"

## JavaScript Functions

### `updateTimeCalcValueB(index, value)`
Handles Value B input changes:
- Stores raw user input in `value_b_raw`
- Converts to seconds based on `value_b_unit`
- Updates `value_b` with converted value
- Handles variables (no conversion when not a number)

### `updateTimeCalcValueBUnit(index, unit)`
Handles unit dropdown changes:
- Stores selected unit in `value_b_unit`
- Re-calculates `value_b` from `value_b_raw`
- Re-renders UI to show updated conversion

## Backend Compatibility

The firmware (`script_engine.c`) doesn't need changes because:
- It already uses `value_b` directly
- The conversion happens in the UI before saving
- The JSON sent to the device contains pre-converted seconds
- `value_b_raw` and `value_b_unit` are UI-only metadata

## Testing

### Test Cases

1. ✅ Enter numeric value → See conversion in help text
2. ✅ Change unit → See value_b update automatically
3. ✅ Enter variable name → No conversion applied
4. ✅ Switch from "add" to "diff" → Unit selector disappears
5. ✅ Load existing script → Shows value_b_raw if available, else value_b
6. ✅ Save and reload → Preserves conversion metadata

### Test Script: Weather Check with 10 Minute Interval

```json
{
  "name": "Weather Check - Intuitive Time Addition",
  "version": "1.0.0",
  "description": "Demonstrates intuitive time_calc with value_b units",
  "target_sensor_type": "generic",
  "actions": [
    {
      "type": "time_calc",
      "result_var": "CurrentTime",
      "time_op": "now",
      "output_unit": "seconds"
    },
    {
      "type": "if",
      "condition": {
        "left": "NextWeatherCheck",
        "operator": "==",
        "right": "0"
      },
      "then": [
        {
          "type": "variable_op",
          "name": "NextWeatherCheck",
          "operation": "=",
          "value": "CurrentTime"
        },
        {
          "type": "log",
          "message": "First run - initialized NextWeatherCheck"
        }
      ],
      "else": []
    },
    {
      "type": "log",
      "message": "Current: {CurrentTime}, Next check: {NextWeatherCheck}"
    },
    {
      "type": "if",
      "condition": {
        "left": "CurrentTime",
        "operator": ">=",
        "right": "NextWeatherCheck"
      },
      "then": [
        {
          "type": "log",
          "message": "Time to check weather!"
        },
        {
          "type": "variable_op",
          "name": "LastWeatherCheck",
          "operation": "=",
          "value": "CurrentTime"
        },
        {
          "type": "time_calc",
          "result_var": "NextWeatherCheck",
          "time_op": "add",
          "value_a": "CurrentTime",
          "value_b": "600",
          "value_b_raw": "10",
          "value_b_unit": "minutes",
          "output_unit": "seconds"
        },
        {
          "type": "weather_fetch",
          "provider": "open-meteo",
          "api_key": "",
          "latitude": -34.08183,
          "longitude": 151.004129
        },
        {
          "type": "log",
          "message": "Weather updated. Next check at {NextWeatherCheck}"
        }
      ],
      "else": [
        {
          "type": "log",
          "message": "Not yet time. Will check at {NextWeatherCheck}"
        }
      ]
    }
  ]
}
```

## Files Modified

- `/app/templates/sensor_master_control.html`
  - Updated `time_calc` block rendering (line ~4555)
  - Added `updateTimeCalcValueB()` function (line ~5540)
  - Added `updateTimeCalcValueBUnit()` function (line ~5565)
  - Updated defaults initialization (line ~3704)
  - Updated examples section (line ~4600)

## Benefits

1. **Intuitive UX**: Users think in minutes/hours, not seconds
2. **Less Mental Math**: No need to calculate 10 minutes = 600 seconds
3. **Fewer Errors**: Automatic conversion prevents mistakes
4. **Clearer Intent**: Seeing "10 minutes" is clearer than "600"
5. **Backward Compatible**: Existing scripts still work
6. **Flexible**: Can still use "raw" mode for advanced use cases

## Future Enhancements

1. Add milliseconds unit option
2. Show conversion in both directions (e.g., "600 seconds = 10 minutes")
3. Support compound durations (e.g., "1 hour 30 minutes")
4. Add presets for common durations (5 min, 15 min, 1 hour, 1 day)
5. Validate that Value A is a timestamp when using "add"

---

**Date:** January 4, 2026  
**Status:** ✅ Implemented and Deployed
