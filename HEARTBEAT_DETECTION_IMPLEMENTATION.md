# Sensor Heartbeat Detection - Implementation Summary

## Overview
Implemented automatic offline detection for sensors in the Sensor Master Control system. The system now:
1. Checks sensor heartbeat status on page load
2. Continuously monitors heartbeat and updates status every 30 seconds
3. Automatically marks sensors as offline if they haven't checked in within 5 minutes

## Changes Made

### Backend Changes (`app/api/sensor_master_api.py`)

#### 1. New Function: `calculate_sensor_status()`
- **Location**: Lines 390-421
- **Purpose**: Calculates sensor online/offline status based on last heartbeat
- **Logic**:
  - Returns `'pending'` if sensor has never checked in
  - Returns `'online'` if last check-in was within timeout period (default: 10 minutes)
  - Returns `'offline'` if last check-in exceeds timeout period
- **Features**:
  - Handles multiple datetime formats (ISO, SQLite)
  - Configurable timeout period
  - Robust error handling

#### 2. Modified: `get_registered_sensors()`
- **Location**: Lines 424-505
- **Change**: Now calculates real-time status for each sensor using `calculate_sensor_status()`
- **Impact**: API always returns current sensor status based on heartbeat

#### 3. New Endpoint: `/api/sensor-master/check-heartbeats` (POST)
- **Location**: Lines 510-548
- **Purpose**: Batch check and update all sensor statuses in database
- **Returns**: Number of sensors checked and updated
- **Use Case**: Can be called by scheduled tasks or monitoring systems

### Frontend Changes (`app/templates/sensor_master_control.html`)

#### 1. New Function: `updateSensorStatusIndicators()`
- **Location**: Lines 665-689
- **Purpose**: Client-side heartbeat monitoring
- **Logic**:
  - Checks each sensor's `last_check_in` timestamp
  - Compares with current time
  - Marks sensors as offline if they exceed 5-minute timeout
  - Logs status changes to console
- **Integration**: Called automatically every 30 seconds via `refreshData()`

#### 2. Modified: `refreshData()`
- **Location**: Lines 653-664
- **Change**: Now calls `updateSensorStatusIndicators()` after loading data
- **Impact**: Status is recalculated on every refresh cycle (30 seconds)

#### 3. Modified: `loadStats()`
- **Location**: Lines 1139-1158
- **Change**: Uses already-loaded sensor array to avoid redundant API calls
- **Optimization**: Improves performance by reducing network requests

### Test Suite (`test_heartbeat_detection.py`)

Created comprehensive test suite covering:
- **Status calculation logic**: Tests all edge cases (no check-in, recent, old, boundary)
- **Datetime format handling**: Validates ISO and SQLite formats
- **Database integration**: Verifies status calculation matches database records

## Configuration

### Heartbeat Timeout
The timeout period is configurable in two places:

**Backend (API):**
```python
# Default: 10 minutes
calculate_sensor_status(last_check_in, timeout_minutes=10)
```

**Frontend (JavaScript):**
```javascript
// Default: 10 minutes (600,000 milliseconds)
const HEARTBEAT_TIMEOUT_MS = 10 * 60 * 1000;
```

To change the timeout, update both values consistently.

## How It Works

### On Page Load
1. Frontend loads sensor data from API
2. Backend calculates status based on `last_check_in` timestamp
3. Frontend displays current status with visual indicators

### Ongoing Monitoring
1. Every 30 seconds, `refreshData()` is called
2. `updateSensorStatusIndicators()` checks each sensor's `last_check_in`
3. Sensors exceeding timeout are marked as offline
4. UI updates to reflect new status
5. Stats counters are recalculated

### Heartbeat Flow
```
Sensor → POST /api/sensor-master/heartbeat → Updates last_check_in
                                          ↓
                                    Status = 'online'
                                          ↓
                                   No heartbeat for 5+ min
                                          ↓
                                    Status = 'offline'
```

## Visual Indicators

Sensors display status using:
- **Color-coded icons**: 
  - 🟢 Green circle = Online
  - 🔴 Red circle = Offline  
  - 🟡 Yellow circle = Pending (never checked in)
- **Status text**: "online", "offline", "pending"
- **Stats cards**: Real-time counters for each status category

## Testing

Run the test suite:
```bash
/home/an0naman/Documents/GitHub/template/.venv/bin/python test_heartbeat_detection.py
```

Expected output:
```
✅ All tests passed!
✓ esp32_fermentation_0 | DB: online | Calc: online | Last Check: ...
✅ Database check completed!
```

## Troubleshooting

### Sensor not showing as offline when turned off

**Check:**
1. Verify sensor was previously online (has `last_check_in` timestamp)
2. Wait 5 minutes after sensor stops sending heartbeats
3. Refresh the page or wait for next auto-refresh (30 seconds)
4. Check browser console for status change logs

### Status not updating in UI

**Check:**
1. Open browser console (F12)
2. Look for log messages: "Sensor X marked as offline..."
3. Verify `refreshData()` is being called every 30 seconds
4. Check network tab for API calls to `/api/sensor-master/sensors`

### Backend shows different status than frontend

**Cause**: The backend calculates status on-demand, while frontend also checks client-side.

**Solution**: This is expected. Both should converge to the same value. If they don't match, the backend calculation is authoritative.

## API Examples

### Get sensors with real-time status:
```bash
curl http://localhost:5000/api/sensor-master/sensors
```

### Manually trigger heartbeat check:
```bash
curl -X POST http://localhost:5000/api/sensor-master/check-heartbeats
```

## Future Enhancements

Possible improvements:
1. Make timeout configurable via UI settings
2. Add email/webhook notifications when sensors go offline
3. Historical status tracking (uptime monitoring)
4. Grace period before marking critical sensors offline
5. Different timeout values per sensor type
6. WebSocket support for real-time status updates

## Files Modified

1. `/app/api/sensor_master_api.py` - Backend status calculation and API
2. `/app/templates/sensor_master_control.html` - Frontend monitoring
3. `/test_heartbeat_detection.py` - Test suite (new file)

## Backward Compatibility

This change is **fully backward compatible**:
- Existing sensors continue to work without modification
- Old status values in database are overridden with calculated values
- No database schema changes required
- No breaking changes to API responses
