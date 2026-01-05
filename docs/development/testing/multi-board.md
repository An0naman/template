# Testing Multi-Board Support

## 🧪 Testing Checklist

### Phase 1: Database & Backend Testing ✅

- [x] Database migration applied successfully
- [x] `board_type` column added to SensorRegistration
- [x] Existing sensors updated with default board type
- [ ] API endpoints accept board_type
- [ ] UI displays board badges

### Phase 2: ESP32-WROOM-32 Testing

- [ ] Firmware compiles for ESP32-WROOM-32
- [ ] Correct pins configured (GPIO4, GPIO25, GPIO2, GPIO34)
- [ ] Device registers with board_type = "esp32_wroom32"
- [ ] Dashboard shows blue "ESP32" badge
- [ ] Sensor details show correct board info
- [ ] Temperature sensor works (GPIO4)
- [ ] Relay control works (GPIO25)
- [ ] LED indicator works (GPIO2)

### Phase 3: Firebeetle 2 ESP32-C6 Testing

- [ ] Firmware compiles for ESP32-C6
- [ ] Correct pins configured (GPIO15, GPIO14, GPIO15, GPIO2)
- [ ] Device registers with board_type = "firebeetle2_esp32c6"
- [ ] Dashboard shows cyan "ESP32-C6" badge
- [ ] Sensor details show correct board info
- [ ] Temperature sensor works (GPIO15)
- [ ] Relay control works (GPIO14)
- [ ] RGB LED works (GPIO15)
- [ ] Battery monitoring works (GPIO2)

---

## 🔍 Detailed Testing Steps

### Step 1: Verify Database Migration

```bash
# Check if board_type column exists
sqlite3 /home/an0naman/Documents/GitHub/template/data/template.db \
  "PRAGMA table_info(SensorRegistration);" | grep board_type

# Check existing sensors have board_type
sqlite3 /home/an0naman/Documents/GitHub/template/data/template.db \
  "SELECT sensor_id, sensor_type, board_type FROM SensorRegistration;"
```

**Expected Output:**
```
esp32_fermentation_002|esp32_fermentation|esp32_wroom32
esp32_fermentation_mk2|esp32_wroom32|esp32_wroom32
```

### Step 2: Test Backend API

```bash
# Start the application (if not running)
docker-compose up -d

# Or for development:
python run.py
```

**Test registration endpoint:**
```bash
curl -X POST http://localhost:5001/api/sensor-master/register \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "test_esp32_wroom",
    "sensor_name": "Test ESP32 WROOM",
    "sensor_type": "esp32_wroom32",
    "board_type": "esp32_wroom32",
    "hardware_info": "ESP32-WROOM-32 (ESP32)",
    "firmware_version": "2.1.0",
    "ip_address": "192.168.1.100",
    "capabilities": ["temperature", "relay_control"]
  }'
```

**Expected Response:**
```json
{
  "status": "registered",
  "has_config": true,
  "message": "Sensor registered successfully"
}
```

**Verify in database:**
```bash
sqlite3 /home/an0naman/Documents/GitHub/template/data/template.db \
  "SELECT sensor_id, board_type FROM SensorRegistration WHERE sensor_id='test_esp32_wroom';"
```

### Step 3: Test UI Display

1. **Open Sensor Master Control page:**
   - Navigate to: `http://localhost:5001/sensor-master` (or 5005 for production)

2. **Check Sensor List Table:**
   - Look for "Board" column
   - Verify blue badge shows "ESP32" for WROOM-32 sensors
   - Verify badges have microchip icon

3. **Check Sensor Details:**
   - Click "View" button on any sensor
   - Look for "Board Type:" field
   - Should show badge and architecture (Xtensa/RISC-V)

4. **Test with browser console:**
   ```javascript
   // Open browser console (F12)
   fetch('/api/sensor-master/sensors')
     .then(r => r.json())
     .then(data => {
       console.table(data.sensors.map(s => ({
         id: s.sensor_id,
         board_type: s.board_type,
         hardware_info: s.hardware_info
       })));
     });
   ```

### Step 4: Test ESP32-WROOM-32 Firmware

**4.1 Compile Test:**
```bash
# Using Arduino CLI (if installed)
arduino-cli compile --fqbn esp32:esp32:esp32 sensor_firmware.ino

# Check for board-specific defines
grep -A 5 "CONFIG_IDF_TARGET_ESP32" sensor_firmware.ino
```

**4.2 Upload to Physical Device:**

1. Open Arduino IDE
2. File → Open → `sensor_firmware.ino`
3. Tools → Board → ESP32 Arduino → "ESP32 Dev Module"
4. Tools → Upload Speed → 921600
5. Tools → Port → Select your ESP32
6. Click Upload

**4.3 Monitor Serial Output:**
```
========================================
ESP32 Sensor Master Control
========================================
Board: ESP32-WROOM-32
Chip: ESP32
Sensor ID: esp32_fermentation_mk2
Board Type: esp32_wroom32
Firmware: v2.1.0 (Built: Dec 26 2025)
========================================
```

**4.4 Check Registration:**
- Watch serial output for registration success
- Check dashboard for new sensor with blue badge
- Verify pin assignments in serial output

### Step 5: Test Firebeetle 2 ESP32-C6 Firmware

**5.1 Prerequisites:**
```bash
# Install ESP32 board support 3.0.0+ in Arduino IDE:
# File → Preferences → Additional Board Manager URLs:
# https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# Tools → Board → Boards Manager → Search "esp32" → Install latest (3.0.0+)
```

**5.2 Compile Test:**
1. Tools → Board → ESP32 Arduino → "DFRobot Firebeetle 2 ESP32-C6"
2. Tools → USB CDC On Boot → "Enabled"
3. Sketch → Verify/Compile

**Expected compiler output:**
```
Detecting chip type... ESP32-C6
Board: firebeetle2_esp32c6 selected
Configuring pins for ESP32-C6...
```

**5.3 Upload to C6 Device:**
1. Connect Firebeetle 2 ESP32-C6 via USB-C
2. Hold BOOT button if needed
3. Click Upload
4. Release BOOT after upload starts

**5.4 Monitor Serial Output:**
```
========================================
ESP32 Sensor Master Control
========================================
Board: Firebeetle 2 ESP32-C6
Chip: ESP32-C6
Sensor ID: esp32_fermentation_mk2
Board Type: firebeetle2_esp32c6
Firmware: v2.1.0 (Built: Dec 26 2025)
========================================
```

**5.5 Verify Pin Configuration:**
- Temperature sensor on GPIO15
- Relay on GPIO14
- RGB LED on GPIO15
- Battery monitor on GPIO2

### Step 6: Hardware Testing

**Temperature Sensor Test (DS18B20):**
```cpp
// Expected serial output:
✓ Temperature: 22.5°C
```

**Relay Control Test:**
```cpp
// In script or manually:
{"type": "gpio_write", "pin": 25, "value": "HIGH"}  // ESP32
{"type": "gpio_write", "pin": 14, "value": "HIGH"}  // C6
```

**LED Blink Test:**
```cpp
// Should blink built-in LED
{"type": "gpio_write", "pin": 2, "value": "HIGH"}   // ESP32
{"type": "gpio_write", "pin": 15, "value": "HIGH"}  // C6
```

**Battery Monitor Test (if hardware connected):**
```cpp
{"type": "read_battery", "pin": 34, "r1": 100000, "r2": 100000}  // ESP32
{"type": "read_battery", "pin": 2, "r1": 100000, "r2": 100000}   // C6
```

### Step 7: Integration Testing

**7.1 Mixed Board Environment:**
1. Register one ESP32-WROOM-32
2. Register one Firebeetle 2 ESP32-C6
3. View dashboard - should see both badges
4. Assign same script to both
5. Verify both execute correctly despite different pins

**7.2 Script Assignment:**
```javascript
// Create a test script
{
  "name": "Multi-Board Test",
  "version": "1.0.0",
  "actions": [
    {"type": "read_temperature", "alias": "Temp"},
    {"type": "log", "message": "Temp: {Temp}"},
    {"type": "gpio_write", "pin": 2, "value": "HIGH"},
    {"type": "delay", "ms": 1000},
    {"type": "gpio_write", "pin": 2, "value": "LOW"}
  ]
}
```

**7.3 Test Board Type Filtering:**
- Create scripts with target_sensor_type
- Verify only compatible boards shown in assignment dropdown

---

## 🐛 Common Issues & Solutions

### Issue: Compilation fails for ESP32-C6
**Symptoms:** `error: 'CONFIG_IDF_TARGET_ESP32C6' undeclared`

**Solution:**
```bash
# Update ESP32 board support
# Arduino IDE: Tools → Board → Boards Manager → ESP32 → Update to 3.0.0+
```

### Issue: Wrong pins used after upload
**Symptoms:** Temperature sensor doesn't work

**Diagnosis:**
```bash
# Check what board was selected during compilation
# Serial output should show:
Board: [Expected Board Name]
```

**Solution:**
- Re-verify correct board selected in Arduino IDE
- Re-upload firmware

### Issue: Board shows as "Unknown" in dashboard
**Symptoms:** Grey "Unknown" badge

**Diagnosis:**
```bash
# Check database
sqlite3 template.db "SELECT sensor_id, board_type FROM SensorRegistration WHERE sensor_id='YOUR_ID';"
```

**Solution:**
- Ensure firmware v2.1.0 uploaded
- Trigger re-registration (restart device)
- Check serial output for registration payload

### Issue: USB CDC not working on ESP32-C6
**Symptoms:** No serial output

**Solution:**
1. Tools → USB CDC On Boot → "Enabled"
2. Re-upload firmware
3. Wait 5-10 seconds after upload
4. Open Serial Monitor

---

## 📊 Test Results Template

```
Date: ___________
Tester: ___________

### ESP32-WROOM-32
- [ ] Compilation: PASS / FAIL
- [ ] Upload: PASS / FAIL
- [ ] Board Detection: PASS / FAIL (Value: _______)
- [ ] Pin Configuration: PASS / FAIL
- [ ] Registration: PASS / FAIL
- [ ] UI Display: PASS / FAIL (Badge color: _______)
- [ ] Temperature Sensor: PASS / FAIL
- [ ] Relay Control: PASS / FAIL
- [ ] LED: PASS / FAIL

### Firebeetle 2 ESP32-C6
- [ ] Compilation: PASS / FAIL
- [ ] Upload: PASS / FAIL
- [ ] Board Detection: PASS / FAIL (Value: _______)
- [ ] Pin Configuration: PASS / FAIL
- [ ] Registration: PASS / FAIL
- [ ] UI Display: PASS / FAIL (Badge color: _______)
- [ ] Temperature Sensor: PASS / FAIL
- [ ] Relay Control: PASS / FAIL
- [ ] RGB LED: PASS / FAIL
- [ ] Battery Monitor: PASS / FAIL

### Integration
- [ ] Both boards on dashboard: PASS / FAIL
- [ ] Board badges correct: PASS / FAIL
- [ ] Script assignment: PASS / FAIL
- [ ] Mixed execution: PASS / FAIL

Notes:
__________________________________________
__________________________________________
```

---

## 🎯 Quick Smoke Test (5 minutes)

**Fastest way to verify everything works:**

```bash
# 1. Check database
sqlite3 data/template.db "SELECT COUNT(*) FROM SensorRegistration WHERE board_type IS NOT NULL;"

# 2. Start app
python run.py

# 3. Open browser
# Navigate to: http://localhost:5001/sensor-master

# 4. Look for:
#    - "Board" column in table
#    - Blue badges on existing sensors
#    - No JavaScript errors in console (F12)

# 5. Test registration (mock)
curl -X POST http://localhost:5001/api/sensor-master/register \
  -H "Content-Type: application/json" \
  -d '{"sensor_id":"test123","sensor_type":"esp32_wroom32","board_type":"esp32_wroom32","sensor_name":"Test"}'

# 6. Refresh page - should see test123 with blue badge

# ✅ If all above work, system is functional!
```

---

## 📞 Need Help?

If tests fail, collect this info:
1. Serial output from device
2. Browser console errors (F12)
3. Database query results
4. Arduino IDE board selection
5. Firmware version shown in serial output

Check documentation:
- `BOARD_SUPPORT.md` - Technical details
- `QUICK_START_MULTI_BOARD.md` - Setup guide
- `MULTI_BOARD_SUPPORT_SUMMARY.md` - Implementation details
