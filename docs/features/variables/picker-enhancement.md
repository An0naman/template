# Variable Picker Enhancement for Delay & Hibernate Blocks

## Overview

Enhanced the delay and hibernate blocks in the Logic Builder with improved variable selection UX, matching the functionality of the log message block.

## New Features

### 1. Delay Block - Variable Dropdown Picker

#### Before
- Text input with autocomplete datalist only
- Users had to type variable names manually

#### After
- **Text input** with autocomplete (preserved)
- **NEW: Dropdown button** with "Insert Variable" menu
- Click to insert variable directly into the field

#### Visual Layout
```
┌──────────────────────────────────────────────────┐
│ ⏰ Duration (ms)            [Insert Variable ▼] │
│ ┌──────────────────────────────────────────────┐ │
│ │ 1000 or variable name                        │ │
│ └──────────────────────────────────────────────┘ │
│ ℹ Enter a number (milliseconds) or variable...  │
└──────────────────────────────────────────────────┘
```

When clicking "Insert Variable" dropdown:
```
┌──────────────────────────────┐
│ Variables                    │
│   delayTime                  │
│   waitDuration               │
│ System                       │
│   millis                     │
│   battery                    │
└──────────────────────────────┘
```

---

### 2. Hibernate Block - Mode Toggle with Variable Picker

#### Before
- Single text input for duration
- Unit dropdown separate
- Confusing when to use numeric vs variable

#### After
- **NEW: Mode toggle buttons** (Numeric / Variable)
- **Numeric Mode**: Number input + Unit dropdown
- **Variable Mode**: Text input + Variable picker dropdown
- Clear visual separation of the two modes

#### Visual Layout

**Numeric Mode (Default)**
```
┌──────────────────────────────────────────────────┐
│ 🛏️ Sleep Duration    [●Numeric] [○Variable]     │
│                                                  │
│ ┌──────────────┐  ┌─────────────────────────┐  │
│ │ 60           │  │ Minutes            ▼   │  │
│ └──────────────┘  └─────────────────────────┘  │
│ ℹ Enter a number and select the time unit       │
└──────────────────────────────────────────────────┘
```

**Variable Mode**
```
┌──────────────────────────────────────────────────┐
│ 🛏️ Sleep Duration    [○Numeric] [●Variable]     │
│                                                  │
│ ┌──────────────────────────────┐  [📋▼]        │
│ │ sleepTime                    │                │
│ └──────────────────────────────┘                │
│ ℹ Variable should contain time in minutes.      │
│   Unit: [minutes ▼]                             │
└──────────────────────────────────────────────────┘
```

---

## Implementation Details

### Delay Block Changes

**File**: `app/templates/sensor_master_control.html`

**Code Structure**:
```javascript
// Build variable options for dropdown
let delayVarOptions = '';
if (uniqueVars.length > 0) {
    delayVarOptions += '<li><h6 class="dropdown-header">Variables</h6></li>';
    uniqueVars.forEach(v => {
        delayVarOptions += `<li><a class="dropdown-item small" href="#" 
            onclick="document.getElementById('delay-ms-${index}').value = '${v}'; 
            updateBlockProperty(${index}, 'ms', '${v}', 'text', false); 
            return false;">${v}</a></li>`;
    });
}

// Add system variables too
const systemVars = SYSTEM_VARIABLES || [];
// ... similar structure
```

**Features**:
- Dropdown button with "Insert Variable" label
- Grouped sections: Variables, System
- Clicking an option sets the input field and updates the block
- Uses small dropdown styling for compact UI

---

### Hibernate Block Changes

**Mode Toggle Implementation**:
```javascript
// Determine current mode based on duration value
const isVariableMode = block.duration && isNaN(parseFloat(block.duration));

// Radio button group for mode selection
<div class="btn-group btn-group-sm" role="group">
    <input type="radio" name="hibernate-mode-${index}" id="hibernate-numeric-${index}" 
           ${!isVariableMode ? 'checked' : ''} 
           onchange="toggleHibernateMode(${index}, false)">
    <label for="hibernate-numeric-${index}">
        <i class="fas fa-clock"></i> Numeric
    </label>
    
    <input type="radio" name="hibernate-mode-${index}" id="hibernate-variable-${index}" 
           ${isVariableMode ? 'checked' : ''} 
           onchange="toggleHibernateMode(${index}, true)">
    <label for="hibernate-variable-${index}">
        <i class="fas fa-calculator"></i> Variable
    </label>
</div>
```

**New JavaScript Functions**:

1. **`toggleHibernateMode(index, isVariableMode)`**
   - Shows/hides the appropriate container
   - Resets duration value when switching modes
   - Syncs JSON representation

2. **`setHibernateVariable(index, varName)`**
   - Sets the variable name from dropdown click
   - Updates the block property
   - Keeps UI in sync

**Container Logic**:
- `hibernate-numeric-container-${index}`: Shown in numeric mode
- `hibernate-variable-container-${index}`: Shown in variable mode
- Display toggled via `style.display` property

---

## User Experience Improvements

### Discoverability
✅ **Before**: Users had to know that variables could be typed in
✅ **After**: Dropdown shows all available variables - easier to discover

### Clarity
✅ **Before**: Hibernate block mixed numeric and variable inputs
✅ **After**: Clear separation with mode toggle

### Efficiency
✅ **Before**: Type variable name manually (error-prone)
✅ **After**: Click to insert (faster, no typos)

### Consistency
✅ **Now matches**: Log message block pattern (familiar UX)

---

## Usage Examples

### Example 1: Setting Delay from Variable Dropdown

**Steps**:
1. Add a "Set Variable" block: `delayTime = 5000`
2. Add a "Delay" block
3. Click "Insert Variable" dropdown
4. Click "delayTime" from the list
5. Input field automatically populated with `delayTime`

**Result**:
```json
{
  "actions": [
    {"type": "variable_op", "name": "delayTime", "operation": "=", "value": "5000"},
    {"type": "delay", "ms": "delayTime"}
  ]
}
```

---

### Example 2: Hibernate - Numeric Mode

**Steps**:
1. Add "Hibernate" block
2. Ensure "Numeric" mode is selected (default)
3. Enter `30` in number field
4. Select "Minutes" from unit dropdown

**Result**:
```json
{
  "type": "hibernate",
  "duration": 30,
  "unit": "minutes"
}
```

---

### Example 3: Hibernate - Variable Mode

**Steps**:
1. Add "Set Variable" block: `sleepTime = 120`
2. Add "Hibernate" block
3. Click "Variable" mode toggle
4. Click variable picker dropdown (📋)
5. Select "sleepTime" from list
6. Select "seconds" as unit (tells firmware the variable is in seconds)

**Result**:
```json
{
  "actions": [
    {"type": "variable_op", "name": "sleepTime", "operation": "=", "value": "120"},
    {"type": "hibernate", "duration": "sleepTime", "unit": "seconds"}
  ]
}
```

**Note**: The `unit` field in variable mode tells the firmware what unit the variable value represents.

---

## Mode Detection Logic

### Hibernate Block Mode Detection

When loading existing logic:
```javascript
const isVariableMode = block.duration && isNaN(parseFloat(block.duration));
```

**Examples**:
- `duration: 60` → Numeric mode (can parse as float)
- `duration: "sleepTime"` → Variable mode (cannot parse as float)
- `duration: "120"` → Numeric mode (can parse as float)
- `duration: ""` → Numeric mode (empty defaults to numeric)

This ensures existing scripts display correctly when opened.

---

## UI Components

### Bootstrap Components Used

1. **Button Group** (Mode Toggle)
   - `btn-group btn-group-sm`
   - Radio buttons styled as toggle buttons
   - `btn-check` class for radio inputs

2. **Dropdown Menu** (Variable Picker)
   - `dropdown` wrapper
   - `dropdown-toggle` button
   - `dropdown-menu-end` for right-aligned menu
   - `max-height: 200px; overflow-y: auto` for scrolling

3. **Icons**
   - FontAwesome icons: `fa-clock`, `fa-calculator`, `fa-list`
   - Visual indicators for mode and actions

---

## Benefits

| Benefit | Impact |
|---------|--------|
| 🎯 **Faster Variable Selection** | Click instead of type |
| 🔍 **Better Discovery** | See all available variables |
| 🎨 **Clearer Intent** | Mode toggle makes usage obvious |
| ✅ **Fewer Errors** | No typos in variable names |
| 📱 **Mobile Friendly** | Easier to tap dropdown than type |
| 🎓 **Lower Learning Curve** | Visual cues guide users |
| 🔄 **Consistency** | Matches log message pattern |

---

## Testing

### Test Scenarios

1. **Delay Block**
   - ✅ Dropdown shows user variables
   - ✅ Dropdown shows system variables
   - ✅ Clicking variable inserts it into field
   - ✅ Manual typing still works
   - ✅ Autocomplete datalist still works
   - ✅ Empty variable list hides dropdown button

2. **Hibernate Block - Numeric Mode**
   - ✅ Number input accepts integers
   - ✅ Unit dropdown has 3 options
   - ✅ Changing either field updates JSON
   - ✅ Validation accepts numeric values

3. **Hibernate Block - Variable Mode**
   - ✅ Text input accepts variable names
   - ✅ Variable picker dropdown works
   - ✅ Unit selector still shows (for firmware interpretation)
   - ✅ Validation accepts variable names

4. **Mode Toggle**
   - ✅ Switching mode shows/hides correct container
   - ✅ Switching mode preserves or resets duration appropriately
   - ✅ Loading existing numeric values opens in numeric mode
   - ✅ Loading existing variable names opens in variable mode

5. **Integration**
   - ✅ Works within IF blocks
   - ✅ Works with nested logic
   - ✅ JSON sync works correctly
   - ✅ Save/load preserves mode

---

## Future Enhancements

Potential improvements:
1. **Preview Variable Value**: Show `sleepTime = 120` in tooltip
2. **Smart Unit Conversion**: Suggest best unit based on value
3. **Expression Support**: Allow `delayTime * 2` in variable mode
4. **Recently Used**: Show recently used variables at top
5. **Variable Validation**: Warn if variable not defined yet

---

## Backward Compatibility

✅ **Fully Compatible**: All existing scripts work unchanged

### Migration

**Old Scripts** (numeric):
```json
{"type": "delay", "ms": 1000}
{"type": "hibernate", "duration": 60, "unit": "seconds"}
```
**Result**: Opens in numeric mode (default) ✅

**Old Scripts** (variable - from previous update):
```json
{"type": "delay", "ms": "delayTime"}
{"type": "hibernate", "duration": "sleepTime", "unit": "minutes"}
```
**Result**: 
- Delay: Shows variable in input field ✅
- Hibernate: Opens in variable mode automatically ✅

---

## Files Modified

**Single File**: `/app/templates/sensor_master_control.html`

**Changes**:
1. Lines ~4422-4460: Delay block rendering with variable picker
2. Lines ~4461-4535: Hibernate block with mode toggle and variable picker
3. Lines ~5070-5105: New helper functions (`toggleHibernateMode`, `setHibernateVariable`)

---

## Summary

This enhancement makes variable usage more **intuitive** and **accessible** by:
- Adding dropdown pickers for easy variable selection
- Introducing mode toggle for hibernate to clarify numeric vs variable usage
- Maintaining consistency with other blocks (log message)
- Preserving all existing functionality and backward compatibility

Users can now build complex dynamic timing logic with less typing and fewer errors! 🎉
