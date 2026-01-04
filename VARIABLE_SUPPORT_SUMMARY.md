# Logic Builder Enhancement: Variable Support Summary

## What Was Changed

I've successfully added support for using **variables** within delay and hibernate blocks in the Logic Builder. This means you can now calculate a value (like a delay time or hibernate duration) using variables, and then use that variable in timing blocks.

## Key Changes

### 1. **Delay Block** - Variable Support for `ms` Field
- Changed from: Number-only input
- Changed to: Text input with autocomplete for variables
- Accepts: Numbers (e.g., `1000`) OR variable names (e.g., `delayTime`)
- Added help text explaining both options

### 2. **Hibernate Block** - Variable Support for `duration` Field  
- Changed from: Number-only input
- Changed to: Text input with autocomplete for variables
- Accepts: Numbers (e.g., `60`) OR variable names (e.g., `sleepMinutes`)
- Unit selector (seconds/minutes/hours) remains unchanged

### 3. **Enhanced Validation**
- Updated `validateLogic()` to accept both numbers and valid variable names
- Variable names must follow pattern: `[a-zA-Z_][a-zA-Z0-9_]*`
- Clear error messages: "Duration must be a number or variable name"

### 4. **Autocomplete Support**
- Both fields now include `list="logicVariables"` 
- Shows dropdown with:
  - User-defined variables
  - System variables (millis, battery, etc.)
  - Pin aliases and sensor names

## Use Cases

### Example 1: Calculate Delay Before Using It
```javascript
// Set a variable
{ "type": "variable_op", "name": "delayTime", "operation": "=", "value": "2000" }

// Use it in delay
{ "type": "delay", "ms": "delayTime" }
```

### Example 2: Dynamic Hibernate Based on Battery
```javascript
// Read battery level
{ "type": "read_battery", "pin": 34, "alias": "batteryLevel" }

// Set default sleep time
{ "type": "variable_op", "name": "sleepMinutes", "operation": "=", "value": "10" }

// If battery low, sleep longer
{
  "type": "if",
  "condition": { "left": "batteryLevel", "operator": "<", "right": "20" },
  "then": [
    { "type": "variable_op", "name": "sleepMinutes", "operation": "=", "value": "30" }
  ]
}

// Hibernate using calculated duration
{ "type": "hibernate", "duration": "sleepMinutes", "unit": "minutes" }
```

### Example 3: Adjust Delay Based on Temperature
```javascript
// Read temperature
{ "type": "read_temperature", "pin": 4, "alias": "temp" }

// Start with 1 second delay
{ "type": "variable_op", "name": "waitTime", "operation": "=", "value": "1000" }

// If temp > 25, double the delay
{
  "type": "if",
  "condition": { "left": "temp", "operator": ">", "right": "25" },
  "then": [
    { "type": "variable_op", "name": "waitTime", "operation": "*=", "value": "2" }
  ]
}

// Wait using calculated time
{ "type": "delay", "ms": "waitTime" }
```

## Files Modified

**File**: `/app/templates/sensor_master_control.html`

**Changes**:
1. Lines ~4422-4433: Added special rendering for delay blocks
2. Lines ~4434-4452: Added special rendering for hibernate blocks  
3. Lines ~3742-3772: Enhanced validation function
4. Lines ~4458-4461: Skip delay/hibernate fields in standard rendering

## Testing

To test the feature:

1. Open the Logic Builder
2. Add a "Set Variable / Math" block to create a variable (e.g., `myDelay = 5000`)
3. Add a "Delay / Wait" block
4. In the Duration field, type the variable name (e.g., `myDelay`)
5. Notice autocomplete suggestions appear
6. Save the logic - it should validate successfully
7. Check the JSON output - variable name should be preserved as text

## Backend Considerations

⚠️ **Important**: For this to work on the ESP32 firmware, the device needs to support variable resolution when executing delay/hibernate commands.

The firmware should:
1. Check if the `ms`/`duration` value is numeric
2. If not, look up the variable value from runtime state
3. Convert to numeric before executing

Example pseudo-code:
```cpp
if (action["type"] == "delay") {
    int delayMs;
    if (action["ms"].is<int>()) {
        delayMs = action["ms"];
    } else {
        String varName = action["ms"];
        delayMs = variables[varName].as<int>();
    }
    delay(delayMs);
}
```

## Documentation Created

- **LOGIC_BUILDER_VARIABLES_FEATURE.md**: Comprehensive documentation with examples, validation rules, and implementation details

## Future Enhancements

Potential improvements:
1. Support variables in other numeric fields (PWM duty cycle, pin numbers, etc.)
2. Add visual indicators showing which variables are used where
3. Warn if a variable is used before being defined
4. Support basic expressions (e.g., `delayTime * 2`)
5. Show current variable values in UI

## Benefits

✅ **Dynamic Timing**: Adjust delays based on runtime conditions  
✅ **Battery Conservation**: Longer sleeps when battery is low  
✅ **Sensor-Driven**: Timing based on environmental readings  
✅ **Reusable Values**: Define once, use multiple times  
✅ **More Flexible**: Complex logic without hardcoded values  
✅ **Better UX**: Autocomplete makes variables easy to discover
