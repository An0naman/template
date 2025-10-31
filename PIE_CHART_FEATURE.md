# Pie Chart for Categorical Data - Feature Implementation

**Date:** October 31, 2025  
**Feature:** Pie chart visualization for non-numeric/categorical sensor data  
**Status:** ✅ Complete

---

## 🎯 Objective

Add a pie chart option for categorical/text-based sensor data to show the distribution of different states over time (e.g., how much time a door was "open" vs "closed").

## ✨ Feature Overview

### What is it?
A pie chart that displays the **distribution** of categorical sensor values, showing:
- **Count** of each state (e.g., "on": 150, "off": 75)
- **Percentage** of total readings for each state (e.g., "on": 66.7%, "off": 33.3%)
- **Visual representation** with color-coded slices

### When is it available?
- ✅ Only shown for **categorical/text-based** sensor data
- ✅ Automatically appears in chart type dropdown when viewing sensors like:
  - Door Status (open/closed)
  - Relay Status (on/off)
  - Device State (active/idle/error)
  - Any non-numeric sensor values

## 📊 Chart Type Availability Matrix

| Data Type | Line | Bar | Area | Pie |
|-----------|------|-----|------|-----|
| **Numeric** (Temperature, Humidity, etc.) | ✅ | ✅ | ✅ | ❌ |
| **Categorical** (on/off, open/closed, etc.) | ✅ Timeline | ✅ | ❌ | ✅ **NEW!** |

## 🎨 Visual Example

### Sample Data:
```
Door Status readings over 24 hours:
- "open": 180 readings
- "closed": 120 readings
Total: 300 readings
```

### Pie Chart Display:
```
        🟢 OPEN
      ╱─────────╲
     │           │  60%
     │           │
      ╲─────────╱
        🔴 CLOSED
          40%
```

**Legend:**
- 🟢 OPEN: 180 (60.0%)
- 🔴 CLOSED: 120 (40.0%)

## 💻 Implementation Details

### 1. Updated Chart Type Options

**File:** `app/static/js/sections/_sensors_functions.js`

```javascript
function getAvailableChartTypes(dataType) {
    if (dataType === 'numeric') {
        return [
            { value: 'line', label: 'Line Chart' },
            { value: 'bar', label: 'Bar Chart' },
            { value: 'area', label: 'Area Chart' }
        ];
    } else {
        // Categorical data gets pie chart option
        return [
            { value: 'line', label: 'Timeline (Line)' },
            { value: 'bar', label: 'Bar Chart' },
            { value: 'pie', label: 'Pie Chart' }  // ← NEW!
        ];
    }
}
```

### 2. New Pie Chart Rendering Function

Created `renderCategoricalPieChart(data)` which:

#### Step 1: Count Occurrences
```javascript
const categoryCount = {};
data.forEach(reading => {
    const value = String(reading.value).toLowerCase().trim();
    categoryCount[value] = (categoryCount[value] || 0) + 1;
});
// Result: { "open": 180, "closed": 120 }
```

#### Step 2: Calculate Percentages
```javascript
const total = counts.reduce((sum, count) => sum + count, 0);
const percentages = counts.map(count => ((count / total) * 100).toFixed(1));
// Result: ["60.0", "40.0"]
```

#### Step 3: Assign Colors
```javascript
const colors = labels.map(label => getCategoryColor(label, 0.8));
// Uses existing color scheme: green for "open", red for "closed", etc.
```

#### Step 4: Create Chart.js Pie Chart
```javascript
sensorChartV2 = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: labels.map(label => label.toUpperCase()),
        datasets: [{
            data: counts,
            backgroundColor: colors,
            borderColor: borderColors,
            borderWidth: 2
        }]
    },
    // ... options
});
```

### 3. Routing Logic

Updated `renderCategoricalChart()` to detect pie chart requests:
```javascript
function renderCategoricalChart(data, preferredChartType) {
    // Route to pie chart function if requested
    if (preferredChartType === 'pie') {
        renderCategoricalPieChart(data);
        return;
    }
    // ... existing timeline/bar chart logic
}
```

## 🎯 Features

### Legend Display
- Shows on the **right side** of the chart
- Format: `LABEL: count (percentage%)`
- Example: `OPEN: 180 (60.0%)`

### Tooltips
- Hover over any slice to see details
- Format: `LABEL: X readings (XX.X%)`
- Example: `OPEN: 180 readings (60.0%)`

### Title
- Automatically generated from sensor type
- Format: `[Sensor Type] State Distribution`
- Example: `Door Status State Distribution`

### Color Scheme
- Uses existing `getCategoryColor()` function
- Consistent with timeline and bar charts
- Common states have semantic colors:
  - 🟢 Green: "on", "open", "active", "true", "yes"
  - 🔴 Red: "off", "closed", "inactive", "false", "no"
  - 🟡 Yellow: "warning", "pending", "idle"
  - 🔵 Blue: Default for unknown states

## 🔄 User Flow

### Scenario 1: User views categorical sensor
1. User selects "Door Status" sensor (has "open"/"closed" values)
2. System detects data is categorical
3. Chart Type dropdown shows: **Timeline (Line), Bar Chart, Pie Chart**
4. User selects "Pie Chart"
5. Pie chart renders showing distribution of states

### Scenario 2: User switches from numeric to categorical sensor
1. User viewing "Temperature" sensor (numeric)
2. Chart Type dropdown shows: Line, Bar, Area
3. User selects "Relay Status" sensor (categorical: on/off)
4. Chart Type dropdown **updates** to: Timeline, Bar, Pie Chart
5. Previous chart type is preserved if valid, otherwise defaults to Timeline

### Scenario 3: User analyzes state distribution
1. User selects categorical sensor and "Pie Chart"
2. Chart shows: 70% "on", 30% "off"
3. User hovers over "on" slice
4. Tooltip shows: "ON: 210 readings (70.0%)"
5. User can see at a glance which state dominates

## 📈 Benefits

### For Users:
- ✅ **Quick Insights** - Instantly see state distribution
- ✅ **Percentage View** - Easy to understand proportions
- ✅ **Visual Appeal** - Colorful, engaging visualization
- ✅ **Comparison** - Easy to compare multiple states

### For Analysis:
- ✅ **Pattern Recognition** - Identify dominant states
- ✅ **Anomaly Detection** - Spot unusual distributions
- ✅ **Reporting** - Great for presentations and dashboards
- ✅ **Monitoring** - Quick status overview

## 🧪 Testing Scenarios

### Test Case 1: Two-State Sensor (Binary)
**Data:** Door status with "open" and "closed"  
**Expected:** Pie chart with 2 slices, green and red  
**Result:** ✅ Pass

### Test Case 2: Multi-State Sensor
**Data:** Device status with "active", "idle", "error", "offline"  
**Expected:** Pie chart with 4 slices, different colors  
**Result:** ✅ Pass

### Test Case 3: Single State (Edge Case)
**Data:** All readings are "on"  
**Expected:** Single-slice pie chart at 100%  
**Result:** ✅ Pass

### Test Case 4: Many States
**Data:** 10+ different categorical values  
**Expected:** Pie chart with multiple slices, legend on right  
**Result:** ✅ Pass

### Test Case 5: Switch from Pie to Timeline
**Expected:** Smooth transition, no errors  
**Result:** ✅ Pass

## 🎨 Chart Configuration

### Dimensions:
- **Responsive:** Fills container width
- **Aspect Ratio:** Maintained automatically
- **Legend Position:** Right side

### Colors:
- **Opacity:** 0.8 for fills, 1.0 for borders
- **Border Width:** 2px for clear separation

### Font Sizes:
- **Legend:** 14px
- **Title:** 16px bold
- **Tooltips:** Default Chart.js size

## 🔧 Technical Specifications

### Chart.js Configuration:
```javascript
{
    type: 'pie',
    data: {
        labels: ['OPEN', 'CLOSED'],
        datasets: [{
            data: [180, 120],
            backgroundColor: [
                'rgba(40, 167, 69, 0.8)',   // green
                'rgba(220, 53, 69, 0.8)'    // red
            ],
            borderColor: [
                'rgba(40, 167, 69, 1)',     // solid green
                'rgba(220, 53, 69, 1)'      // solid red
            ],
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'right' },
            tooltip: { /* custom callbacks */ },
            title: { text: 'State Distribution' }
        }
    }
}
```

### Performance:
- **Fast Rendering:** No complex calculations, just counting
- **Memory Efficient:** Aggregates data before charting
- **Smooth Updates:** Destroys and recreates chart cleanly

## 📝 Code Changes Summary

### Files Modified:
1. **`app/static/js/sections/_sensors_functions.js`**
   - Updated `getAvailableChartTypes()` - Added pie option
   - Created `renderCategoricalPieChart()` - New function (~90 lines)
   - Updated `renderCategoricalChart()` - Added pie routing

### Lines of Code:
- **Added:** ~95 lines
- **Modified:** ~5 lines
- **Total Impact:** Minimal, well-contained

### No Breaking Changes:
- ✅ Existing chart types still work
- ✅ Numeric data unaffected
- ✅ Backward compatible

## 🚀 Future Enhancements (Optional)

Potential improvements:
- [ ] Add **doughnut chart** variant (hollow center)
- [ ] Add **export as image** feature
- [ ] Add **animation on load** (exploding slices)
- [ ] Add **click to filter** by state
- [ ] Add **3D pie chart** option
- [ ] Add **nested pie chart** for multi-level data

## ✅ Completion Checklist

- [x] Added pie chart to available chart types for categorical data
- [x] Created renderCategoricalPieChart() function
- [x] Integrated pie chart routing in renderCategoricalChart()
- [x] Tested with binary states (2 values)
- [x] Tested with multi-state data (3+ values)
- [x] Verified color consistency
- [x] Verified percentage calculations
- [x] Verified legend display
- [x] Verified tooltips
- [x] Tested chart type switching
- [x] Documentation created

---

**Status:** Production Ready ✅  
**Feature Impact:** Enhanced visualization options for categorical sensor data  
**User Benefit:** Better insights into state distribution patterns
