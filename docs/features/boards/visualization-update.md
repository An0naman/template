# Board Visualization Update - Complete

## Overview
Updated the sensor master control interface to display actual board images (SVG diagrams) instead of simple badge icons, matching the Serial Plotter modal's visual style.

## Changes Made

### 1. Created Board Image Assets
**File**: `app/static/images/boards/firebeetle2-esp32-c6.svg`
- Created detailed SVG diagram of DFRobot Firebeetle 2 ESP32-C6 board
- Features:
  - Green PCB background (DFRobot color scheme)
  - ESP32-C6 chip representation with specs (RISC-V 160MHz, WiFi 6, BLE 5.0)
  - USB-C connector
  - Pin headers with GPIO labels and color coding:
    * Red/Orange: Power pins (5V, 3V3)
    * Black: Ground pins
    * Blue: GPIO pins
    * Orange: ADC pins
    * Purple: UART pins
    * Green: I2C pins
    * Orange: SPI pins
  - Boot and Reset buttons
  - Status LEDs (Power and User)
  - WiFi 6 antenna pattern
  - Battery connector indicator
- Dimensions: 340x580px viewBox (matches ESP32-WROOM-32 format)

**File**: `app/static/images/boards/esp32-wroom-32.svg`
- Already existed with detailed ESP32-WROOM-32 board diagram

### 2. Added getBoardConfig() Function
**File**: `app/templates/sensor_master_control.html` (line ~1270)

Created centralized board configuration function that returns:
```javascript
{
    name: "Board Name",
    image: "/static/images/boards/board-file.svg",
    chipOverlay: { x, y, width, height },  // For Serial Plotter chip log overlay
    pins: { left: [...], right: [...] }    // For Serial Plotter pin controls
}
```

**Supported Boards**:
1. **ESP32-WROOM-32** - Default/fallback board
   - Image: `/static/images/boards/esp32-wroom-32.svg`
   - 19 pins on left side, 19 pins on right side
   - Includes power, GPIO, ADC, UART, SPI, I2C pins

2. **firebeetle2_esp32c6** - DFRobot Firebeetle 2 ESP32-C6
   - Image: `/static/images/boards/firebeetle2-esp32-c6.svg`
   - 10 pins on left side, 10 pins on right side
   - Compact form factor with WiFi 6 support

### 3. Updated Sensor Details Modal
**File**: `app/templates/sensor_master_control.html` - `viewSensorDetails()` function (line ~2551)

**Before**: Simple SVG badge icon generated inline
```javascript
const boardSvg = getBoardSvg(sensor.board_type);  // Simple badge
```

**After**: Actual board image loaded from assets
```javascript
const boardConfig = getBoardConfig(sensor.board_type);
<img src="${boardConfig.image}" alt="${boardConfig.name}" class="img-fluid">
```

**Features**:
- Displays actual board image (SVG) in details modal
- Gradient purple background for visual appeal
- White rounded container for the board image
- Board name and specifications displayed below image
- Image fallback: Shows gray placeholder if image fails to load
- Max height: 400px with auto width (maintains aspect ratio)
- Responsive design using Bootstrap classes

### 4. Consistent Board Type Handling

**Board Type Values**:
- `firebeetle2_esp32c6` - From firmware `BOARD_TYPE` constant
- `ESP32-WROOM-32` - Default/fallback value
- `esp32_wroom32` - Alternative format (if used)

**UI Display Names**:
- "DFRobot Firebeetle 2 ESP32-C6" (for firebeetle2_esp32c6)
- "ESP32-WROOM-32" (for ESP32-WROOM-32)
- Architecture and specs shown in badges and descriptions

## Integration Points

### Serial Plotter Modal
- Uses `getBoardConfig()` to load board images
- Uses pin configuration for interactive overlays
- Chip log overlay positioned using `chipOverlay` coordinates
- Already functional - no changes needed

### Sensor Details Modal
- Now uses `getBoardConfig()` for consistency
- Displays same board images as Serial Plotter
- Simplified view (no pin overlays, just the board image)
- Shows board name and specs from config

### Database Schema
- `SensorRegistration.board_type` column stores board identifier
- Populated during device registration from firmware
- Migration: `app/migrations/add_board_type_column.py`

## Testing Checklist

- [x] Created Firebeetle 2 ESP32-C6 SVG board image
- [x] Added getBoardConfig() function with both board types
- [x] Updated viewSensorDetails() to use board images
- [x] Restarted Docker containers
- [ ] **TODO**: Test in browser - open sensor details modal
- [ ] **TODO**: Verify board image loads correctly for ESP32-C6
- [ ] **TODO**: Verify fallback works if image fails
- [ ] **TODO**: Test Serial Plotter modal still works

## Next Steps

1. **Browser Testing**: 
   - Navigate to Sensor Master Control page
   - Click "View Details" on ESP32-C6 sensor
   - Verify board image displays correctly

2. **Serial Plotter Verification**:
   - Open Serial Plotter for ESP32-C6
   - Verify board image loads
   - Check if pin overlays work (if script has GPIO controls)

3. **Future Enhancements**:
   - Add more board types as devices are added
   - Create photo-realistic board images (vs SVG diagrams)
   - Add interactive pin overlays to details modal (currently only in plotter)

## File Locations

```
app/
├── static/
│   └── images/
│       └── boards/
│           ├── esp32-wroom-32.svg          ✅ Existing
│           └── firebeetle2-esp32-c6.svg    ✅ New
└── templates/
    └── sensor_master_control.html          ✅ Updated
        ├── getBoardConfig()                 (line ~1270)
        └── viewSensorDetails()              (line ~2551)
```

## Architecture Benefits

1. **Centralized Configuration**: Single `getBoardConfig()` function for all board data
2. **Reusability**: Serial Plotter and Details modal use same images/config
3. **Extensibility**: Easy to add new board types - just add config and SVG
4. **Consistency**: Same visual style across different modals
5. **Maintainability**: Board images separated from code logic

## Technical Notes

- SVG images are scalable and resolution-independent
- Image URLs use absolute paths from `/static/` directory
- Flask serves static files from `app/static/` directory
- Docker volume mount ensures static files are accessible
- Fallback mechanism prevents broken image display
- Bootstrap classes ensure responsive design

## Related Files

- `src/main.cpp` - Firmware defines `BOARD_TYPE` constant
- `app/api/sensor_master.py` - API returns `board_type` in sensor list
- `app/models.py` - SensorRegistration model has `board_type` field
- `app/migrations/add_board_type_column.py` - Database migration

---

**Status**: ✅ Implementation Complete - Awaiting Browser Testing
**Date**: 2024
**Updated By**: GitHub Copilot
