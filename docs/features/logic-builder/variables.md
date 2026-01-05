# Logic Builder: Variable Support in Delay and Hibernate Blocks

## Overview

The Logic Builder now supports using **variables** in place of hardcoded numbers for delay and hibernate durations. This allows for dynamic timing based on calculations or sensor readings.

## Changes Made

### 1. Enhanced Block Rendering

#### Delay Block
- **Field**: `ms` (milliseconds)
- **Input Type**: Text field with autocomplete datalist
- **Accepts**: 
  - Numeric values (e.g., `1000` for 1 second)
  - Variable names (e.g., `delayTime`, `waitDuration`)
- **Help Text**: "Enter a number (milliseconds) or a variable name (e.g., delayTime)"

#### Hibernate Block
- **Field**: `duration`
- **Input Type**: Text field with autocomplete datalist
- **Accepts**:
  - Numeric values (e.g., `60` for 60 seconds/minutes/hours)
  - Variable names (e.g., `sleepTime`, `hibernateDuration`)
- **Help Text**: "Enter a number or a variable name"
- **Unit Field**: Still uses dropdown (seconds/minutes/hours)

### 2. Updated Validation Logic

The `validateLogic()` function now accepts:
- **Numbers**: Any positive numeric value
- **Variable Names**: Must follow naming rules (alphanumeric + underscore, start with letter/underscore)
- **Pattern**: `/^[a-zA-Z_][a-zA-Z0-9_]*$/`

Invalid entries will show error: "Duration must be a number or variable name"

### 3. Variable Autocomplete

Both fields now include `list="logicVariables"` which provides autocomplete suggestions for:
- User-defined variables (from `variable_op` blocks)
- System variables (millis, battery, etc.)
- Pin aliases and sensor names

## Usage Examples

### Example 1: Calculate Delay Duration

```json
{
  "actions": [
    {
      "type": "variable_op",
      "name": "delayTime",
      "operation": "=",
      "value": "5000"
    },
    {
      "type": "log",
      "message": "Waiting for {delayTime} ms"
    },
    {
      "type": "delay",
      "ms": "delayTime"
    }
  ]
}
```

### Example 2: Dynamic Delay Based on Temperature

```json
{
  "actions": [
    {
      "type": "read_temperature",
      "pin": 4,
      "alias": "currentTemp"
    },
    {
      "type": "variable_op",
      "name": "delayTime",
      "operation": "=",
      "value": "1000"
    },
    {
      "type": "if",
      "condition": {
        "left": "currentTemp",
        "operator": ">",
        "right": "25"
      },
      "then": [
        {
          "type": "variable_op",
          "name": "delayTime",
          "operation": "*=",
          "value": "2"
        }
      ],
      "else": []
    },
    {
      "type": "delay",
      "ms": "delayTime"
    },
    {
      "type": "log",
      "message": "Delayed for {delayTime}ms"
    }
  ]
}
```

### Example 3: Variable Hibernate Duration

```json
{
  "actions": [
    {
      "type": "variable_op",
      "name": "sleepMinutes",
      "operation": "=",
      "value": "10"
    },
    {
      "type": "read_battery",
      "pin": 34,
      "alias": "batteryLevel"
    },
    {
      "type": "if",
      "condition": {
        "left": "batteryLevel",
        "operator": "<",
        "right": "20"
      },
      "then": [
        {
          "type": "variable_op",
          "name": "sleepMinutes",
          "operation": "=",
          "value": "30"
        }
      ],
      "else": []
    },
    {
      "type": "log",
      "message": "Hibernating for {sleepMinutes} minutes"
    },
    {
      "type": "hibernate",
      "duration": "sleepMinutes",
      "unit": "minutes"
    }
  ]
}
```

### Example 4: Calculate Delay from Sensor Reading

```json
{
  "actions": [
    {
      "type": "analog_read",
      "pin": 34,
      "alias": "potValue"
    },
    {
      "type": "variable_op",
      "name": "delayTime",
      "operation": "=",
      "value": "potValue"
    },
    {
      "type": "variable_op",
      "name": "delayTime",
      "operation": "*=",
      "value": "10"
    },
    {
      "type": "log",
      "message": "Delay set to {delayTime}ms based on potentiometer"
    },
    {
      "type": "delay",
      "ms": "delayTime"
    }
  ]
}
```

## Use Cases

### 1. **Adaptive Timing**
   - Adjust delays based on sensor readings
   - Scale timing based on environmental conditions

### 2. **Battery Conservation**
   - Longer hibernate times when battery is low
   - Shorter intervals when power is plentiful

### 3. **User Input**
   - Set timing via potentiometer or button presses
   - Allow runtime configuration without re-uploading

### 4. **Complex Calculations**
   - Multiply/divide timings based on formulas
   - Chain multiple calculations together

### 5. **Conditional Timing**
   - Different delays for different conditions
   - State-based timing adjustments

## Backend Requirements

For this feature to work on the ESP32 firmware, the device must support:

1. **Variable Resolution**: When executing a delay or hibernate command, the firmware should:
   - Check if the `ms`/`duration` value is numeric
   - If not numeric, look up the variable value from the runtime state
   - Convert variable value to numeric before executing

2. **Example Firmware Code** (pseudo-code):
```cpp
if (action["type"] == "delay") {
    int delayMs = 0;
    
    // Check if ms is a number or variable
    if (action["ms"].is<int>()) {
        delayMs = action["ms"];
    } else if (action["ms"].is<String>()) {
        String varName = action["ms"];
        // Look up variable in runtime state
        if (variables.containsKey(varName)) {
            delayMs = variables[varName].as<int>();
        }
    }
    
    delay(delayMs);
}
```

## Validation Rules

### Valid Variable Names
✅ `delayTime`
✅ `wait_duration`
✅ `_private`
✅ `time1`

### Invalid Variable Names
❌ `123time` (starts with number)
❌ `delay-time` (contains hyphen)
❌ `wait time` (contains space)
❌ `delay.time` (contains dot)

### Valid Numeric Values
✅ `1000`
✅ `500`
✅ `60`

### Invalid Numeric Values
❌ `-100` (negative)
❌ `` (empty)
❌ `null`

## UI Improvements

1. **Autocomplete**: Dropdown list shows available variables as you type
2. **Help Text**: Clear instructions on what values are accepted
3. **Visual Styling**: Primary label color and info icon for clarity
4. **Validation**: Real-time feedback when saving logic

## Testing Checklist

- [ ] Enter numeric value in delay.ms field
- [ ] Enter variable name in delay.ms field
- [ ] Verify autocomplete shows available variables
- [ ] Enter numeric value in hibernate.duration field
- [ ] Enter variable name in hibernate.duration field
- [ ] Save logic with numeric delay - should succeed
- [ ] Save logic with variable delay - should succeed
- [ ] Save logic with invalid variable name - should fail validation
- [ ] Verify JSON output preserves variable names (not converted to numbers)
- [ ] Create variable before using in delay
- [ ] Use system variable in delay/hibernate
- [ ] Verify unit dropdown still works for hibernate

## Future Enhancements

1. **More Fields**: Support variables in other numeric fields (pin numbers, PWM duty cycle, etc.)
2. **Expressions**: Support basic math expressions (e.g., `delayTime * 2`)
3. **Type Checking**: Warn if variable hasn't been defined yet
4. **Variable Preview**: Show current value of variables in the UI
5. **Smart Suggestions**: Only suggest numeric variables for duration fields

## Related Files Modified

- `/app/templates/sensor_master_control.html`
  - Added special rendering for `delay` block (lines ~4422-4433)
  - Added special rendering for `hibernate` block (lines ~4434-4452)
  - Updated `validateLogic()` function (lines ~3742-3772)
  - Added field skipping in standard rendering (lines ~4458-4461)

## Documentation Updates Needed

- Update JSON_SCRIPT_COMMANDS.md to show variable usage examples
- Add tutorial for creating dynamic timing scripts
- Document firmware variable resolution requirements
