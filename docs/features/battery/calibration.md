# Battery Voltage Calibration Feature

## Overview
Added comprehensive battery voltage calibration support to the Sensor Master Control system. Users can now calibrate battery voltage divider readings by entering the actual voltage measured with a multimeter, and the system will automatically apply these calibration values to all battery readings.

## Changes Made

### 1. Database Migration (`app/migrations/add_battery_calibration.py`)
**Added 4 new columns to `SensorRegistration` table:**
- `battery_r1` (REAL, default: 100000.0) - Top resistor value in voltage divider (Battery+ → ADC)
- `battery_r2` (REAL, default: 100000.0) - Bottom resistor value in voltage divider (ADC → GND)
- `battery_calibrated_voltage` (REAL) - Reference voltage measured with multimeter
- `battery_calibration_date` (TIMESTAMP) - When calibration was last performed

**Migration executed successfully on `data/template.db`**

### 2. User Interface (`app/templates/sensor_master_control.html`)
**Added Battery Calibration Section to Sensor Details Modal:**

Located in the sensor details modal (when clicking on a sensor's info icon), the new calibration panel includes:

- **Measured Voltage (Vs)** input field - Enter voltage from multimeter (e.g., 4.15V)
- **R1 (Top Resistor)** input field - Resistor from Battery+ to ADC pin
- **R2 (Bottom Resistor)** input field - Resistor from ADC pin to GND
- **Save Calibration** button - Saves values to database
- **Reset to Default** button - Resets to standard 100kΩ/100kΩ
- **Last Calibrated** indicator - Shows when last calibrated
- Helpful explanation of voltage divider formula

**JavaScript Functions Added:**
- `calibrateBattery(sensorId)` - Validates inputs and saves calibration via API
- `resetCalibration(sensorId)` - Resets to default 100kΩ values

### 3. API Endpoints (`app/api/sensor_master_api.py`)

#### New Endpoint: POST `/api/sensor-master/calibrate/<sensor_id>`
Saves battery calibration data for a sensor.

**Request Body:**
```json
{
  "battery_r1": 100000.0,
  "battery_r2": 100000.0,
  "battery_calibrated_voltage": 4.15
}
```

**Features:**
- Validates resistor values (must be positive numbers)
- Validates calibrated voltage (must be positive if provided)
- Records calibration timestamp
- Returns success confirmation with saved values

#### Modified Endpoint: GET `/api/sensor-master/script/<sensor_id>`
**Enhanced to inject calibration data into battery actions:**

When a sensor requests its script, the endpoint now:
1. Checks if the sensor has calibration data (`battery_r1`, `battery_r2`)
2. Recursively searches through script actions for `read_battery` blocks
3. Automatically injects calibrated R1/R2 values into those actions
4. Returns calibration info in response metadata

**Example Response:**
```json
{
  "script_available": true,
  "script": { "actions": [{ "type": "read_battery", "r1": 145900, "r2": 100000, ... }] },
  "version": "1.0.0",
  "calibration": {
    "battery_r1": 145900.0,
    "battery_r2": 100000.0,
    "battery_calibrated_voltage": 4.15
  }
}
```

**Benefits:**
- Scripts automatically use calibrated values without manual editing
- Firmware receives correct resistor ratios on every script fetch
- Historical scripts remain unchanged; calibration applied dynamically

### 4. How It Works

#### Voltage Divider Formula
The battery voltage is read through a voltage divider circuit:

```
Vbat ---[R1]---+--- ADC Pin
                |
              [R2]
                |
               GND
```

**Formula:** `Vbat = Vadc × (R1 + R2) / R2`

Where:
- `Vbat` = Actual battery voltage
- `Vadc` = Voltage at ADC pin (what ESP32 reads)
- `R1` = Top resistor (Battery → ADC)
- `R2` = Bottom resistor (ADC → GND)

#### Calibration Process

1. **User measures actual voltage** with multimeter (e.g., 4.15V)
2. **User enters measured voltage** in calibration UI
3. **User enters/confirms R1 and R2 values** (initially 100kΩ each)
4. **System saves calibration** to database with timestamp
5. **Next time sensor fetches script**, calibrated values are automatically injected
6. **Firmware uses calibrated values** in battery reading calculations
7. **All future readings** use corrected voltage divider ratio

#### Board-Specific Notes

**ESP32-WROOM-32:**
- Typical battery pin: GPIO34
- Default divider: R1=100kΩ, R2=100kΩ (2:1 ratio)

**FireBeetle 2 ESP32-C6:**
- Battery monitoring pin: GPIO2 or built-in
- Has built-in voltage divider: R1≈145.9kΩ, R2=100kΩ
- Calibration especially useful for this board!

## Usage Instructions

### For End Users

1. **Navigate** to Sensor Master Control page
2. **Click** the info icon (ℹ️) next to your sensor
3. **Scroll** to "Battery Voltage Calibration" section
4. **Measure** your battery voltage with a multimeter
5. **Enter** the measured voltage in "Measured Voltage (Vs)" field
6. **Verify/Update** R1 and R2 values if you know your circuit
7. **Click** "Save Calibration"
8. **Device will use** calibrated values on next script update

### For Developers

**To add calibration support to new firmware:**

The calibration values are automatically injected into the `read_battery` action when the device fetches its script. No firmware changes needed!

Example in your firmware:
```cpp
// The firmware already supports r1/r2 parameters in read_battery actions
if (type == "read_battery") {
    int pin = action["pin"].as<int>();
    float r1 = action["r1"] | 100000.0; // Will receive calibrated value
    float r2 = action["r2"] | 100000.0; // Will receive calibrated value
    float vref = action["vref"] | 3.3;
    
    // Read and calculate with provided r1/r2
    float voltage = (raw / 4095.0) * vref * ((r1 + r2) / r2);
    ...
}
```

**To query calibration data:**
```python
cursor.execute('''
    SELECT battery_r1, battery_r2, battery_calibrated_voltage, battery_calibration_date
    FROM SensorRegistration
    WHERE sensor_id = ?
''', (sensor_id,))
```

## Testing Checklist

- [x] Database migration runs successfully
- [x] Calibration UI displays in sensor details modal
- [x] Can enter and save calibration values
- [x] Values persist in database
- [x] Calibration data appears in GET /sensors response
- [x] Script endpoint injects calibration values
- [ ] Device receives and uses calibrated values (requires device testing)
- [ ] Battery readings are more accurate after calibration (requires device testing)
- [ ] Plotter shows corrected voltage readings (visualization enhancement)

## Future Enhancements

1. **Auto-Calibration Wizard**
   - Step-by-step guided calibration process
   - Calculate R1/R2 ratio from multiple measurements
   - Visual feedback during calibration

2. **Calibration History**
   - Track calibration changes over time
   - Show drift/degradation trends
   - Alert when recalibration recommended

3. **Voltage Correction in Logs**
   - Apply calibration factor to historical voltage logs
   - Show "raw" vs "calibrated" readings in plotter
   - Export corrected data for analysis

4. **Multi-Point Calibration**
   - Calibrate at multiple voltage levels
   - Create lookup table for non-linear responses
   - Account for ADC non-linearity

5. **Circuit Detection**
   - Auto-detect voltage divider ratio from readings
   - Suggest calibration when readings seem off
   - Board-specific presets (FireBeetle C6, etc.)

## Files Modified

1. `app/migrations/add_battery_calibration.py` - New migration file
2. `app/templates/sensor_master_control.html` - Added calibration UI + JS functions
3. `app/api/sensor_master_api.py` - Added calibration endpoint + script injection logic

## Related Documentation

- `BATTERY_LOGGING_FIX.md` - Original battery logging implementation
- `BOARD_SUPPORT.md` - Board-specific battery pins and configurations
- `TESTING_MULTI_BOARD.md` - Testing battery readings across boards

## Notes

- Default values (100kΩ/100kΩ) work for most standard voltage dividers
- FireBeetle 2 ESP32-C6 has different built-in divider - calibration highly recommended
- Calibration is sensor-specific - each device can have unique values
- Values are automatically injected into scripts, no manual editing required
- Calibration survives script updates - stored separately in sensor registration
