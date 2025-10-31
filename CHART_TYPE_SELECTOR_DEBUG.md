# Chart Type Selector - Bug Fix

**Date:** October 31, 2025  
**Issue:** Chart type dropdown showing wrong options for categorical data
**Status:** 🔧 Debugging Added

---

## 🐛 Problem Report

User reported: "For text-based data, it only shows the charts that don't work"

This suggests that when viewing categorical/text-based sensor data (like "on"/"off" or "open"/"closed"), the chart type dropdown is showing the wrong options.

## 🔍 Investigation

### Expected Behavior:
- **Numeric Data** → Show: Line, Bar, Area
- **Categorical Data** → Show: Timeline (Line), Bar (exclude Area)

### Possible Root Causes:

1. ❓ **Detection Logic Inverted** - `detectDataType()` might be returning the wrong type
2. ❓ **Filter Logic Inverted** - `getAvailableChartTypes()` might have swapped conditions  
3. ❓ **Timing Issue** - `updateChartTypeSelector()` might not be called at the right time
4. ❓ **Data Issue** - Categorical data might have numeric-looking values

## 🔧 Changes Made

### 1. Added Debug Logging

Added console.log statements to `updateChartTypeSelector()`:
```javascript
console.log(`[DEBUG] Detected data type for "${currentSensorType}":`, dataType, 
    `(sample values: ${filteredData.slice(0, 3).map(r => r.value).join(', ')})`);
console.log('[DEBUG] Available chart types for', dataType, ':', 
    availableTypes.map(t => t.label).join(', '));
```

This will help us see:
- What data type is being detected
- What sample values are being analyzed
- What chart options are being displayed

### 2. Fixed Categorical Chart Rendering

Updated `renderCategoricalChart()` to respect the `preferredChartType` parameter:
```javascript
const isBarChart = preferredChartType === 'bar';

const dataset = {
    showLine: !isBarChart, // Show line for timeline, hide for bar
    stepped: !isBarChart ? 'after' : false, // Stepped line for timeline only
    pointRadius: isBarChart ? 6 : 8, // Adjust point size
    // ...
};
```

Now the function actually switches between timeline (line with steps) and bar (scatter points only).

## 🧪 Testing Instructions

### To Test with Browser Console:

1. **Open an entry with text-based sensor data** (e.g., relay status with "on"/"off")

2. **Open browser console** (F12)

3. **Select the categorical sensor type** from dropdown

4. **Look for debug output:**
   ```
   [DEBUG] Detected data type for "Relay Status": categorical (sample values: on, off, on)
   [DEBUG] Available chart types for categorical : Timeline (Line), Bar Chart
   ```

5. **Check the Chart Type dropdown:**
   - Should show: "Timeline (Line)" and "Bar Chart"
   - Should NOT show: "Area Chart"

6. **Try switching between chart types:**
   - Timeline (Line) → Should show stepped line with colored points
   - Bar Chart → Should show just colored points without connecting lines

### Expected Debug Output:

**For Numeric Sensor (e.g., Temperature):**
```
[DEBUG] Detected data type for "Temperature": numeric (sample values: 22.5, 23.1, 22.8)
[DEBUG] Available chart types for numeric : Line Chart, Bar Chart, Area Chart
```

**For Categorical Sensor (e.g., Door Status):**
```
[DEBUG] Detected data type for "Door Status": categorical (sample values: open, closed, open)
[DEBUG] Available chart types for categorical : Timeline (Line), Bar Chart
```

## 🔍 What to Report Back:

Please provide:
1. **Console debug output** when selecting a categorical sensor
2. **What chart types are showing** in the dropdown
3. **Sample data values** for the sensor (what are the actual values? "on"/"off", "open"/"closed", etc.)
4. **Screenshot** if possible

This will help identify if the issue is:
- Detection logic (detecting numeric when should be categorical)
- Display logic (showing wrong options for correct detection)
- Data format (values that look like text but parse as numbers)

## 💡 Quick Fix if Needed:

If the logic is simply inverted, we can quickly swap the conditions in `getAvailableChartTypes()`:

```javascript
// Current logic:
if (dataType === 'numeric') {
    return [...numeric options...];
} else {
    return [...categorical options...];
}

// If inverted, swap to:
if (dataType === 'categorical') {
    return [...categorical options...];
} else {
    return [...numeric options...];
}
```

But we need the debug output to confirm this first!

---

**Next Steps:** Test with browser console open and report debug output.
