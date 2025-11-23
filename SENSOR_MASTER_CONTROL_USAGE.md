# Using Sensor Master Control - Quick Guide

## 🎯 Your Device is Registered - Now What?

Once your ESP32 is registered, you can control and monitor it from the **Sensor Master Control** page.

---

## 📍 Accessing the Page

Navigate to: **http://localhost:5001/sensor-master-control**

---

## 🗺️ Page Sections Overview

### 1. **Master Control Instances** (Top Section)
- View/Create/Edit master control servers
- Set priorities for multiple masters
- Enable/disable master instances

### 2. **Registered Sensors** (Main Section) ⭐ 
**This is where you'll see your ESP32!**

#### What You'll See:
- **Sensor ID**: Your device ID (e.g., `esp32_fermentation_001`)
- **Name**: Device friendly name
- **Type**: Device type badge
- **Status**: 
  - 🟢 **Online** - Device is connected and checking in
  - 🔴 **Offline** - Device hasn't checked in recently
  - 🟡 **Pending** - Device registered but not yet active
- **Master**: Which master instance it's assigned to
- **Last Check-in**: When it last communicated

#### Actions You Can Take:
- **👁️ View Button** - See detailed sensor information
- **🗑️ Delete Button** - Remove sensor from registry

#### Filter Options:
- Use the **dropdown** in the header to filter by status (All/Online/Offline/Pending)

---

### 3. **Configuration Templates**
Create configuration templates to control your sensor's behavior:

#### Creating a Config:
1. Click **"+ New Template"**
2. Fill in:
   - **Master Instance**: Which master to use
   - **Template Name**: E.g., "Production Config"
   - **Sensor Type**: `esp32_fermentation`
   - **Configuration JSON**: 
   ```json
   {
     "polling_interval": 60,
     "data_endpoint": "http://192.168.1.100:5001/api/devices/data",
     "target_temperature": 18.0,
     "relay_mode": "cooling"
   }
   ```

#### Assigning Config to Sensor:
- Configs are automatically available to sensors of matching type
- Your ESP32 retrieves the config on startup and periodically

---

### 4. **Sensor Scripts & Instructions** ⭐ (Dynamic Updates)
**This is the powerful feature for updating your ESP32 over WiFi!**

#### Uploading a New Script:
1. Click **"Upload Script"** button
2. Fill in the modal:
   - **Sensor ID**: Select your ESP32 from dropdown
   - **Script Name**: E.g., "SOS Pattern" or "Temperature Alert"
   - **Description**: What the script does
   - **Language**: Arduino or MicroPython
   - **Script Code**: Paste your Arduino code
   - **Version**: 1.0.0
   - **Active**: Check to activate immediately

3. Click **"Upload Script"**

#### Example Script (LED Blink Pattern):
```cpp
// SOS Morse Code Pattern
void executeScript() {
    const int LED_PIN = 2;
    
    // S (3 short)
    for(int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        delay(200);
    }
    
    delay(400);
    
    // O (3 long)
    for(int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(600);
        digitalWrite(LED_PIN, LOW);
        delay(200);
    }
    
    delay(400);
    
    // S (3 short)
    for(int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        delay(200);
    }
    
    delay(2000);
}
```

#### What Happens Next:
1. Your ESP32 checks for script updates every **30 seconds**
2. When it finds a new script, it downloads and stores it in flash memory
3. The ESP32 executes the script in its main loop
4. You can upload a new script anytime to change behavior

---

## 🎮 Common Interactions

### View Sensor Details
Click the **👁️ eye icon** next to your sensor to see:
- Full capabilities list
- Hardware information
- Firmware version
- IP address and MAC address
- Configuration details
- Recent check-ins

### Send Commands (via Configuration)
Update the sensor's configuration to change behavior:
1. Edit or create a config template
2. Change values (e.g., `target_temperature`, `polling_interval`)
3. Save the config
4. Your ESP32 picks up changes on next check-in (usually within 5 minutes)

### Upload New Behavior (via Scripts)
Want to change what your ESP32 does without re-flashing:
1. Write Arduino code for the new behavior
2. Upload it as a script
3. Wait 30 seconds for ESP32 to download
4. New behavior starts immediately!

### Monitor Health
- Check **Last Check-in** column to ensure sensor is communicating
- Green status = healthy connection
- If offline, check ESP32 serial monitor and WiFi connection

---

## 🔄 Real-Time Updates

The page **auto-refreshes** data every 30 seconds, so you'll see:
- Status changes (online/offline)
- New check-ins
- Configuration changes
- New scripts uploaded

---

## 📊 Example Workflow

### Scenario: Adjust Fermentation Temperature

1. **View Current Sensor**
   - Go to "Registered Sensors"
   - Find your `esp32_fermentation_001`
   - Click 👁️ to view details
   - Note current target temperature

2. **Update Configuration**
   - Go to "Configuration Templates"
   - Edit your sensor's config
   - Change `target_temperature` from 18.0 to 20.0
   - Save

3. **Wait for Update**
   - Your ESP32 checks for config updates periodically
   - Within 5 minutes, it downloads the new config
   - Temperature setpoint changes automatically

4. **Verify**
   - Watch "Last Check-in" timestamp update
   - Check serial monitor on ESP32 to see new config loaded

### Scenario: Change LED Pattern Without Re-flashing

1. **Write New Pattern**
   ```cpp
   void executeScript() {
       // Breathing effect
       for(int i = 0; i < 255; i++) {
           analogWrite(LED_PIN, i);
           delay(5);
       }
       for(int i = 255; i >= 0; i--) {
           analogWrite(LED_PIN, i);
           delay(5);
       }
   }
   ```

2. **Upload Script**
   - Click "Upload Script"
   - Select your sensor
   - Paste the breathing effect code
   - Set as active
   - Upload

3. **Watch It Work**
   - Wait 30 seconds
   - LED pattern changes to breathing effect
   - No USB connection needed!
   - No re-flashing required!

---

## 🚨 Troubleshooting

### Sensor Shows Offline
- ✅ Check WiFi connection on ESP32
- ✅ Verify ESP32 serial monitor shows heartbeat sends
- ✅ Check server is reachable from ESP32: `ping 192.168.1.100`
- ✅ Review firewall rules on server

### Config Not Updating
- ✅ Ensure config template matches sensor type
- ✅ Check ESP32 is calling the config endpoint periodically
- ✅ View serial monitor for config download messages
- ✅ Verify JSON format is valid

### Script Not Executing
- ✅ Confirm script is marked as "Active"
- ✅ Check ESP32 serial monitor for script download messages
- ✅ Verify script code is valid Arduino syntax
- ✅ Ensure ESP32 code has `checkForScriptUpdates()` in loop

### Can't See Sensor
- ✅ Refresh the page (F5)
- ✅ Check "All Status" filter is selected
- ✅ Verify ESP32 successfully registered (check serial monitor)
- ✅ Test registration endpoint manually with curl

---

## 📞 Quick Reference Commands

### Test Sensor Registration
```bash
curl -X POST http://localhost:5001/api/sensor-master/register \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "esp32_fermentation_001",
    "sensor_name": "My ESP32",
    "sensor_type": "esp32_fermentation",
    "ip_address": "192.168.1.150"
  }'
```

### Check Sensor Status
```bash
curl http://localhost:5001/api/sensor-master/sensors
```

### Get Sensor Config
```bash
curl http://localhost:5001/api/sensor-master/config/esp32_fermentation_001
```

### Upload Script via API
```bash
curl -X POST http://localhost:5001/api/sensor-master/upload-script \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "esp32_fermentation_001",
    "name": "Test Script",
    "code": "void executeScript() { digitalWrite(2, HIGH); delay(1000); digitalWrite(2, LOW); }",
    "language": "arduino",
    "version": "1.0.0",
    "is_active": true
  }'
```

---

## 🎓 Pro Tips

1. **Use Descriptive Script Names**: "SOS Pattern v2" is better than "test"
2. **Version Your Scripts**: Increment version numbers to track changes
3. **Test in Serial Monitor First**: Debug scripts via USB before uploading
4. **Keep Scripts Small**: Large scripts take longer to download over WiFi
5. **Use Descriptions**: Document what each script does for future reference
6. **Deactivate Old Scripts**: Keep only current scripts active to avoid confusion
7. **Monitor Last Check-in**: Regular check-ins indicate healthy connection
8. **Use Config for Settings**: Use scripts for behavior, configs for parameters

---

## 🎉 You're Ready!

Your ESP32 is now part of the master control system. You can:
- ✅ Monitor it in real-time
- ✅ Update its configuration remotely
- ✅ Change its behavior over WiFi
- ✅ Track its health and status
- ✅ Deploy updates without physical access

**No more USB cables. No more re-flashing. Just pure over-the-air control!** 🚀
