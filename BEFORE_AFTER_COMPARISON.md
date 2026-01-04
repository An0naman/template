# Logic Builder: Before & After Comparison

## Feature: Variable Support in Delay and Hibernate Blocks

### BEFORE ❌

#### Delay Block UI
- **Field Type**: Number input only
- **Accepts**: `1000`, `500`, `2000` (hardcoded numbers)
- **Cannot Use**: Variables, calculations, dynamic values

```html
<input type="number" class="form-control form-control-sm" 
       value="${block.ms || ''}" 
       onchange="updateBlockProperty(${index}, 'ms', this.value, 'number', false)">
```

#### Hibernate Block UI  
- **Field Type**: Number input only
- **Accepts**: `60`, `10`, `30` (hardcoded numbers)
- **Cannot Use**: Variables, calculations, dynamic values

#### Validation
```javascript
} else if (block.type === 'delay') {
    if (!block.ms || block.ms < 0) errors.push(`${blockName}: Invalid duration`);
}
```
- Only validates if value is a positive number
- Rejects variable names

#### Example Script (OLD Way)
```json
{
  "actions": [
    {"type": "read_battery", "pin": 34, "alias": "battery"},
    {"type": "log", "message": "Battery: {battery}"},
    {"type": "delay", "ms": 5000},
    {"type": "log", "message": "Done waiting"}
  ]
}
```
**Problem**: Delay time is always 5000ms, cannot adjust based on battery level

---

### AFTER ✅

#### Delay Block UI
- **Field Type**: Text input with autocomplete
- **Accepts**: Numbers (`1000`) OR variable names (`delayTime`)
- **Autocomplete**: Shows available variables as you type
- **Help Text**: Clear instructions

```html
<input type="text" class="form-control form-control-sm" 
       value="${block.ms || ''}" 
       placeholder="1000 or variable name"
       list="logicVariables"
       onchange="updateBlockProperty(${index}, 'ms', this.value, 'text', false)">
<div class="form-text x-small text-muted">
    <i class="fas fa-info-circle"></i> Enter a number (milliseconds) or a variable name (e.g., delayTime)
</div>
```

#### Hibernate Block UI
- **Field Type**: Text input with autocomplete
- **Accepts**: Numbers (`60`) OR variable names (`sleepMinutes`)
- **Autocomplete**: Shows available variables
- **Help Text**: Clear instructions
- **Unit Selector**: Unchanged (seconds/minutes/hours)

```html
<input type="text" class="form-control form-control-sm" 
       value="${block.duration || ''}" 
       placeholder="60 or variable name"
       list="logicVariables"
       onchange="updateBlockProperty(${index}, 'duration', this.value, 'text', false)">
<div class="form-text x-small text-muted">
    <i class="fas fa-info-circle"></i> Enter a number or a variable name
</div>
```

#### Enhanced Validation
```javascript
const isValidNumberOrVariable = (val) => {
    if (val === undefined || val === null || val === '') return false;
    // Allow numbers
    if (!isNaN(parseFloat(val)) && parseFloat(val) >= 0) return true;
    // Allow variable names (alphanumeric + underscore, must start with letter or underscore)
    if (typeof val === 'string' && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(val)) return true;
    return false;
};

// ...

} else if (block.type === 'delay') {
    if (!isValidNumberOrVariable(block.ms)) {
        errors.push(`${blockName}: Duration must be a number or variable name`);
    }
} else if (block.type === 'hibernate') {
    if (!isValidNumberOrVariable(block.duration)) {
        errors.push(`${blockName}: Duration must be a number or variable name`);
    }
}
```
- Validates both numbers AND variable names
- Clear error messages
- Enforces variable naming rules

#### Example Script (NEW Way)
```json
{
  "actions": [
    {"type": "read_battery", "pin": 34, "alias": "batteryLevel"},
    {"type": "variable_op", "name": "delayTime", "operation": "=", "value": "1000"},
    {
      "type": "if",
      "condition": {"left": "batteryLevel", "operator": "<", "right": "30"},
      "then": [
        {"type": "variable_op", "name": "delayTime", "operation": "=", "value": "5000"}
      ]
    },
    {"type": "log", "message": "Waiting {delayTime}ms based on battery"},
    {"type": "delay", "ms": "delayTime"},
    {"type": "log", "message": "Done waiting"}
  ]
}
```
**Benefit**: Delay adjusts dynamically - 5 seconds if battery < 30%, otherwise 1 second

---

## Visual Comparison

### Before: Delay Block
```
┌─────────────────────────────────┐
│ DELAY                      [×]  │
├─────────────────────────────────┤
│ ms                              │
│ ┌─────────────────────────────┐ │
│ │ 1000                    ▼   │ │  ← Number only
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### After: Delay Block
```
┌─────────────────────────────────────────────┐
│ DELAY                                  [×]  │
├─────────────────────────────────────────────┤
│ ⏰ Duration (ms)                            │
│ ┌─────────────────────────────────────────┐ │
│ │ 1000 or variable name              ▼   │ │  ← Text with autocomplete
│ └─────────────────────────────────────────┘ │
│ ℹ Enter a number (milliseconds) or a       │
│   variable name (e.g., delayTime)          │
└─────────────────────────────────────────────┘
```

When typing in field:
```
┌─────────────────────────────────────────────┐
│ ⏰ Duration (ms)                            │
│ ┌─────────────────────────────────────────┐ │
│ │ delay█                             ▼   │ │
│ └─────────────────────────────────────────┘ │
│   ┌──────────────────────────────────────┐  │
│   │ delayTime (Variable)                 │  │  ← Autocomplete dropdown
│   │ delayMinutes (Variable)              │  │
│   │ millis (System)                      │  │
│   │ battery (System)                     │  │
│   └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## Use Case Comparison

### Scenario: Temperature-Based Pump Timing

#### BEFORE ❌
```json
{
  "actions": [
    {"type": "read_temperature", "pin": 4, "alias": "temp"},
    {"type": "set_pump", "pin": 5, "state": true},
    {"type": "delay", "ms": 2000},
    {"type": "set_pump", "pin": 5, "state": false}
  ]
}
```
**Problem**: Pump always runs for 2 seconds regardless of temperature

#### AFTER ✅
```json
{
  "actions": [
    {"type": "read_temperature", "pin": 4, "alias": "temp"},
    {"type": "variable_op", "name": "pumpTime", "operation": "=", "value": "2000"},
    {
      "type": "if",
      "condition": {"left": "temp", "operator": ">", "right": "25"},
      "then": [
        {"type": "variable_op", "name": "pumpTime", "operation": "=", "value": "4000"}
      ]
    },
    {"type": "set_pump", "pin": 5, "state": true},
    {"type": "log", "message": "Running pump for {pumpTime}ms"},
    {"type": "delay", "ms": "pumpTime"},
    {"type": "set_pump", "pin": 5, "state": false}
  ]
}
```
**Benefit**: Pump runs 4 seconds if hot (>25°C), 2 seconds otherwise

---

### Scenario: Battery-Aware Sleep Duration

#### BEFORE ❌
```json
{
  "actions": [
    {"type": "read_battery", "pin": 34},
    {"type": "log", "message": "Going to sleep"},
    {"type": "hibernate", "duration": 10, "unit": "minutes"}
  ]
}
```
**Problem**: Always hibernates for 10 minutes, wastes battery

#### AFTER ✅
```json
{
  "actions": [
    {"type": "read_battery", "pin": 34, "alias": "batteryPct"},
    {"type": "variable_op", "name": "sleepMinutes", "operation": "=", "value": "10"},
    {
      "type": "if",
      "condition": {"left": "batteryPct", "operator": "<", "right": "20"},
      "then": [
        {"type": "variable_op", "name": "sleepMinutes", "operation": "=", "value": "30"}
      ]
    },
    {"type": "log", "message": "Battery at {batteryPct}%, sleeping {sleepMinutes} min"},
    {"type": "hibernate", "duration": "sleepMinutes", "unit": "minutes"}
  ]
}
```
**Benefit**: Conserves battery by sleeping longer (30 min) when battery < 20%

---

## Validation Comparison

### Valid Inputs

| Input Type | BEFORE | AFTER |
|------------|--------|-------|
| Number | ✅ `1000` | ✅ `1000` |
| Variable | ❌ `delayTime` | ✅ `delayTime` |
| System Variable | ❌ `millis` | ✅ `millis` |
| With Underscore | ❌ `delay_time` | ✅ `delay_time` |
| Starts with _ | ❌ `_private` | ✅ `_private` |

### Invalid Inputs

| Input Type | BEFORE Error | AFTER Error |
|------------|--------------|-------------|
| Negative | ✅ "Invalid duration" | ✅ "Must be number or variable" |
| Empty | ✅ "Invalid duration" | ✅ "Must be number or variable" |
| Starts with number | ⚠️ Accepts as number | ✅ "Must be number or variable" |
| Contains spaces | ⚠️ Truncates | ✅ "Must be number or variable" |
| Contains hyphen | ⚠️ Accepts | ✅ "Must be number or variable" |

---

## Developer Impact

### Code Changes Required
- ✅ Frontend: Already implemented
- ⚠️ Backend/Firmware: Needs update to resolve variables

### Firmware Example (What's Needed)
```cpp
// Before: Simple number handling
int delayMs = action["ms"];
delay(delayMs);

// After: Variable resolution needed
int delayMs = 0;
if (action["ms"].is<int>()) {
    delayMs = action["ms"];
} else if (action["ms"].is<String>()) {
    String varName = action["ms"];
    if (variables.containsKey(varName)) {
        delayMs = variables[varName].as<int>();
    } else {
        Serial.println("Error: Variable not found: " + varName);
        delayMs = 1000; // fallback
    }
}
delay(delayMs);
```

---

## Benefits Summary

| Benefit | Impact |
|---------|--------|
| 🎯 **Dynamic Timing** | Delays adjust based on conditions |
| 🔋 **Battery Conservation** | Longer sleeps when battery low |
| 🌡️ **Sensor-Driven** | Actions respond to sensor readings |
| ♻️ **Code Reuse** | Define value once, use multiple times |
| 📊 **Better Logic** | More sophisticated automation |
| 🎨 **Better UX** | Autocomplete makes variables discoverable |
| 📝 **Self-Documenting** | Variable names explain intent |
| 🐛 **Easier Debugging** | Can log variable values |

---

## Migration Path

### Existing Scripts
✅ **Backward Compatible**: Scripts with numeric values continue to work unchanged

```json
// OLD SCRIPT - Still works!
{"type": "delay", "ms": 1000}

// NEW SCRIPT - Now also possible!
{"type": "delay", "ms": "delayTime"}
```

### No Breaking Changes
- Numeric inputs still work exactly as before
- Validation accepts both numbers and variables
- JSON format unchanged
- API unchanged

---

## Next Steps

1. ✅ Frontend implementation complete
2. ⚠️ Update ESP32 firmware to resolve variables
3. 📝 Update JSON_SCRIPT_COMMANDS.md documentation
4. 🧪 Test with actual ESP32 devices
5. 🎓 Create user tutorials/examples
