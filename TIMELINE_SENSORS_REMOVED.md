# Timeline Section - Sensor Readings Removed

**Date:** October 28, 2025  
**Change:** Removed sensor readings from Activity Timeline section  
**Reason:** Keep timeline focused on notes and status changes only

---

## Changes Made

### 1. **Removed Sensors Filter Button**
- Removed "Sensors" button from filter group
- Now only shows: All | Notes | System

### 2. **Removed Sensor Data Loading**
- Removed API call to `/api/entries/{id}/sensor_data`
- Removed `groupSensorsByDay()` function (no longer needed)
- Timeline no longer fetches or displays sensor readings

### 3. **Removed Sensor-Related Styling**
- Removed `.event-sensor::before` CSS (green dot marker)
- Removed `.sensor-reading` CSS class
- Removed `.sensor-value` CSS class

### 4. **Simplified Event Rendering**
- Removed sensor-specific HTML generation
- Removed sensor reading display logic
- Removed "...and X more" text for multiple readings

### 5. **Updated Filter Logic**
- Removed `sensors` filter case
- Now only filters: `all`, `notes`, `system`

---

## Timeline Now Shows

✅ **Entry Creation** - When entry was created  
✅ **Status Changes** - Automatic tracking via system notes  
✅ **User Notes** - All note types with badges  
✅ **System Events** - System-generated activities  

❌ **Sensor Readings** - No longer displayed

---

## Files Modified

**File:** `/app/templates/sections/_timeline_section.html`

**Changes:**
- Removed ~40 lines of sensor-related code
- Reduced from 508 lines to 429 lines
- Cleaner, more focused implementation

---

## Why This Change?

The timeline section is now **focused on activity history** rather than trying to duplicate sensor functionality. Sensor data is better viewed in the dedicated **Sensors Section** which provides:
- Charts and visualizations
- Real-time data
- Sensor-specific features
- Better presentation for numeric data

The Activity Timeline now clearly shows:
- **What happened** (notes, status changes)
- **When it happened** (timestamps)
- **Who/what did it** (user notes vs system events)

---

## Benefits

✅ **Cleaner Display** - No clutter from sensor readings  
✅ **Faster Loading** - One less API call  
✅ **Better Focus** - Timeline shows activity, not metrics  
✅ **Clearer Purpose** - Activity history vs sensor data  
✅ **Simpler Code** - Less complexity to maintain  

---

## If You Need Sensor Data

**Use the Sensors Section** instead:
1. Enable the Sensors section in Layout Builder
2. View real-time charts and graphs
3. Get better visualization of sensor trends
4. Access sensor-specific features

---

**Status:** ✅ Complete - Sensor readings removed from timeline
