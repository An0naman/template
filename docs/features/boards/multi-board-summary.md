# Multi-Board Support Implementation Summary

## 🎯 Overview

Successfully implemented support for multiple ESP32 board types in the Sensor Master Control system. The firmware now automatically detects the board type and configures pins appropriately, while the backend tracks which board each sensor is using.

## ✅ Completed Changes

### 1. Firmware Updates (`sensor_firmware.ino`)

#### Board Detection
- Added automatic board type detection using preprocessor directives
- Detects ESP32-WROOM-32 vs Firebeetle 2 ESP32-C6 at compile time
- Sets appropriate board identifiers:
  - `BOARD_TYPE`: "esp32_wroom32" or "firebeetle2_esp32c6"
  - `BOARD_NAME`: Human-readable board name
  - `CHIP_MODEL`: Chip architecture (ESP32 or ESP32-C6)

#### Board-Specific Pin Configurations

**ESP32-WROOM-32:**
- OneWire Temperature: GPIO4
- Relay Control: GPIO25
- Status LED: GPIO2
- Battery Voltage: GPIO34

**Firebeetle 2 ESP32-C6:**
- OneWire Temperature: GPIO15
- Relay Control: GPIO14
- Status LED: GPIO15 (RGB LED)
- Battery Voltage: GPIO2

#### Registration Updates
- Firmware now sends `board_type` field during registration
- Enhanced `hardware_info` to include chip model
- Updated firmware version to 2.1.0

### 2. Database Migration (`app/migrations/add_board_type_column.py`)

- Added `board_type` column to `SensorRegistration` table
- Automatically updates existing sensors with appropriate board types
- Migration is idempotent and safe to run multiple times

### 3. API Updates (`app/api/sensor_master_api.py`)

- Updated `/api/sensor-master/register` endpoint to accept `board_type`
- Stores board type during sensor registration
- Falls back to `sensor_type` if `board_type` not provided (backwards compatible)
- Added logging to track board types during registration

### 4. UI Updates (`app/templates/sensor_master_control.html`)

#### Sensor List Table
- Added "Board" column showing board type badge
- ESP32-WROOM-32: Blue badge with "ESP32" label
- Firebeetle 2 ESP32-C6: Cyan badge with "ESP32-C6" label
- Includes tooltips with architecture info (Xtensa vs RISC-V)

#### Sensor Details Modal
- Added "Board Type" field showing detailed board information
- Displays chip architecture alongside board name
- Styled with color-coded badges for easy identification

### 5. Documentation (`BOARD_SUPPORT.md`)

Created comprehensive documentation covering:
- Supported board specifications
- Pin mapping reference table
- Arduino IDE setup instructions
- PlatformIO configuration examples
- Troubleshooting guide
- Instructions for adding future board support

## 🔧 How It Works

### Automatic Detection Flow

1. **Compile Time**: Arduino IDE/PlatformIO sets `CONFIG_IDF_TARGET_ESP32C6` or `CONFIG_IDF_TARGET_ESP32` based on selected board
2. **Firmware**: Preprocessor directives detect the target and configure pins accordingly
3. **Registration**: Device reports board type to master control during registration
4. **Storage**: Backend stores board type in database
5. **Display**: UI shows appropriate board badge and information

### Example Registration Payload

```json
{
  "sensor_id": "esp32_fermentation_mk2",
  "sensor_name": "Fermentation Chamber",
  "sensor_type": "firebeetle2_esp32c6",
  "board_type": "firebeetle2_esp32c6",
  "hardware_info": "Firebeetle 2 ESP32-C6 (ESP32-C6)",
  "firmware_version": "2.1.0",
  "capabilities": ["temperature", "relay_control", "analog_read", "read_battery"]
}
```

## 🚀 Usage

### For ESP32-WROOM-32

1. Open `sensor_firmware.ino` in Arduino IDE
2. Select Board: "ESP32 Dev Module"
3. Upload as usual
4. Board will automatically register as `esp32_wroom32`

### For Firebeetle 2 ESP32-C6

1. Open `sensor_firmware.ino` in Arduino IDE
2. Install ESP32 board support 3.0.0+ (required for C6)
3. Select Board: "DFRobot Firebeetle 2 ESP32-C6"
4. Enable "USB CDC On Boot"
5. Upload
6. Board will automatically register as `firebeetle2_esp32c6`

### Viewing Board Types

1. Navigate to **Sensor Master Control** page
2. View registered sensors table
3. "Board" column shows board type badge
4. Click "View" button for detailed board information

## 📊 Benefits

1. **Single Firmware**: One codebase supports multiple boards
2. **Automatic Configuration**: No manual pin configuration needed
3. **Clear Visibility**: Dashboard shows which board each sensor uses
4. **Future Proof**: Easy to add support for additional boards (ESP32-S3, etc.)
5. **Backward Compatible**: Existing sensors continue to work

## 🔄 Migration Path

### Existing Sensors

Existing sensors without `board_type` will:
1. Get assigned `esp32_wroom32` by default during migration
2. Update to correct board type on next registration/heartbeat
3. Continue functioning normally during transition

### New Sensors

New sensors will:
1. Automatically detect board type at compile time
2. Register with correct board type immediately
3. Display correct board badge in UI

## 🛠️ Technical Details

### Database Schema

```sql
ALTER TABLE SensorRegistration
ADD COLUMN board_type TEXT;
```

### API Endpoint Changes

**Before:**
```python
sensor_type = data.get('sensor_type', 'unknown')
```

**After:**
```python
sensor_type = data.get('sensor_type', 'unknown')
board_type = data.get('board_type', sensor_type)  # Fallback for compatibility
```

### Frontend Badge Logic

```javascript
sensor.board_type === 'firebeetle2_esp32c6' 
    ? '<span class="badge bg-info">ESP32-C6</span>'
    : sensor.board_type === 'esp32_wroom32'
        ? '<span class="badge bg-primary">ESP32</span>'
        : '<span class="badge bg-secondary">Unknown</span>'
```

## 📝 Files Modified

1. `sensor_firmware.ino` - Added board detection and pin configurations
2. `app/migrations/add_board_type_column.py` - Database schema update
3. `app/api/sensor_master_api.py` - API endpoint updates
4. `app/templates/sensor_master_control.html` - UI enhancements
5. `BOARD_SUPPORT.md` - New documentation

## 🎓 Next Steps

### Recommended Actions

1. **Run Migration**: Execute the database migration to add `board_type` column
   ```bash
   python app/migrations/add_board_type_column.py
   ```

2. **Test with ESP32-WROOM-32**: Upload firmware to existing ESP32 device
   - Verify it registers with correct board type
   - Check UI displays "ESP32" badge

3. **Test with Firebeetle 2 ESP32-C6**: Upload firmware to C6 device
   - Verify automatic detection works
   - Confirm correct pin usage
   - Check UI displays "ESP32-C6" badge

4. **Update Existing Sensors**: Trigger re-registration
   - Each sensor will update its board type on next heartbeat
   - Or restart sensors to force immediate registration

### Future Enhancements

1. **Add ESP32-S3 Support**: Follow same pattern for S3 boards
2. **Board-Specific Features**: Enable/disable features based on board capabilities
3. **Pin Remapping UI**: Allow custom pin configuration in UI
4. **Auto-Discovery**: Detect available GPIO pins per board type

## 🐛 Troubleshooting

### Issue: Board shows as "Unknown"
**Solution**: Ensure firmware v2.1.0+ is uploaded and sensor has checked in

### Issue: ESP32-C6 won't compile
**Solution**: Update ESP32 Arduino Core to 3.0.0+ for C6 support

### Issue: Wrong pins configured
**Solution**: Verify correct board selected in Arduino IDE before uploading

### Issue: Migration fails
**Solution**: Check database permissions and that `SensorRegistration` table exists

## 📈 Impact

- **Code Reusability**: 100% firmware code shared between boards
- **Maintenance**: Single codebase to maintain
- **User Experience**: Clear visual indicators of board types
- **Scalability**: Easy to add more boards in future
- **Reliability**: Automatic configuration reduces user error

## ✨ Conclusion

The multi-board support implementation provides a solid foundation for managing different ESP32 variants in the Sensor Master Control system. The automatic detection and configuration approach ensures users don't need to manually configure pins, while the UI updates provide clear visibility into which boards are deployed in the field.

---

**Version**: 2.1.0  
**Date**: December 26, 2025  
**Author**: GitHub Copilot  
**Status**: ✅ Complete and Ready for Testing
