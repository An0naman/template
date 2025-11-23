# ESP32 Network Detection Requirements

## 🎯 What Your ESP32 Must Do to Be Found

### 1. **Web Server Running on Port 80**
Your ESP32 must have a web server listening on the standard HTTP port (80).

```cpp
WebServer server(80);  // Arduino
// or
AsyncWebServer server(80);  // ESPAsyncWebServer
```

### 2. **HTTP Endpoint: `/api`**
The scanner looks for `http://YOUR_ESP32_IP/api` (NOT `/data` or any other endpoint)

```cpp
server.on("/api", HTTP_GET, []() {
    // Your handler here
});
```

### 3. **Return Valid JSON**
The `/api` endpoint MUST return a JSON response with proper Content-Type header.

```cpp
server.send(200, "application/json", jsonString);
```

### 4. **Required JSON Fields**
Your JSON **MUST** include at least ONE of these:
- `device_id` 
- `device_name`

### 5. **Magic Keywords in Name/ID**
The `device_id` or `device_name` **MUST** contain at least ONE of these words:
- `esp32`
- `fermentation`
- `controller`
- `sensor`
- `temp`
- `brewery`
- `fermenter`

---

## ✅ **Minimal Working Example**

### Arduino Code:
```cpp
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

WebServer server(80);

void setup() {
    Serial.begin(115200);
    
    // Connect to WiFi
    WiFi.begin("YOUR_SSID", "YOUR_PASSWORD");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());  // WRITE THIS DOWN!
    
    // Setup /api endpoint
    server.on("/api", HTTP_GET, handleApi);
    server.begin();
    Serial.println("Web server started");
}

void handleApi() {
    StaticJsonDocument<512> doc;
    
    // REQUIRED FIELDS - Must have device_id OR device_name
    doc["device_id"] = "esp32_fermentation_001";  // Contains "esp32" keyword ✓
    doc["device_name"] = "My Fermentation Controller";  // Contains "fermentation" keyword ✓
    
    // Optional but helpful fields
    doc["sensor"]["temperature"] = 20.5;
    doc["sensor"]["valid"] = true;
    doc["relay"]["state"] = "OFF";
    doc["relay"]["pin"] = 2;
    
    String output;
    serializeJson(doc, output);
    
    // IMPORTANT: Set proper content type
    server.send(200, "application/json", output);
}

void loop() {
    server.handleClient();
    delay(10);
}
```

---

## 🧪 **Testing Your ESP32**

### Step 1: Check Serial Monitor
After flashing, look for:
```
Connected!
IP Address: 192.168.1.XXX  <-- THIS IS YOUR IP!
Web server started
```

### Step 2: Test from Computer
```bash
# Replace 192.168.1.XXX with your actual IP
curl http://192.168.1.XXX/api
```

### Expected Output:
```json
{
  "device_id": "esp32_fermentation_001",
  "device_name": "My Fermentation Controller",
  "sensor": {
    "temperature": 20.5,
    "valid": true
  },
  "relay": {
    "state": "OFF",
    "pin": 2
  }
}
```

### Step 3: Run Network Scan
Once the curl test works, the network scanner will find it automatically!

---

## ❌ **Common Issues**

### Issue: "Connection refused" or timeout
- ✅ **Fix**: Check ESP32 is connected to WiFi (same network as your computer)
- ✅ **Fix**: Verify web server is running (`server.begin()` was called)
- ✅ **Fix**: Check firewall isn't blocking port 80

### Issue: Scanner finds nothing
- ✅ **Fix**: Verify `/api` endpoint exists (not `/data` or other)
- ✅ **Fix**: Check JSON includes `device_id` or `device_name`
- ✅ **Fix**: Ensure name contains magic keywords (esp32, fermentation, etc.)

### Issue: "404 Not Found"
- ✅ **Fix**: Endpoint must be exactly `/api` (case-sensitive)
- ✅ **Fix**: Make sure `server.on("/api", ...)` is called before `server.begin()`

### Issue: Scanner shows "Invalid JSON"
- ✅ **Fix**: Set Content-Type header: `server.send(200, "application/json", jsonString)`
- ✅ **Fix**: Validate JSON with `curl` or online JSON validator

---

## 🚀 **Quick Checklist**

Before running the network scanner, verify:

- [ ] ESP32 connected to WiFi (same network as app server)
- [ ] Serial monitor shows IP address
- [ ] Web server running on port 80
- [ ] `/api` endpoint exists and returns JSON
- [ ] JSON contains `device_id` or `device_name`
- [ ] Name/ID contains one of the magic keywords
- [ ] `curl http://YOUR_IP/api` returns valid JSON
- [ ] Content-Type header is `application/json`

---

## 📞 **Still Not Working?**

If your ESP32 still isn't detected after following these steps:

1. **Run this test command** (replace IP):
   ```bash
   curl -v http://192.168.1.XXX/api
   ```

2. **Check the response** - it should show:
   - HTTP 200 status
   - Content-Type: application/json
   - Valid JSON with device_id or device_name

3. **Share the curl output** and we can diagnose the issue

---

## 🎓 **Understanding the Detection Logic**

The scanner does this for each IP:
1. Tries to connect to `http://IP/api` (2 second timeout)
2. Checks if response is HTTP 200 OK
3. Parses JSON response
4. Looks for `device_id` or `device_name` fields
5. Checks if name contains keywords: `['esp32', 'fermentation', 'controller', 'sensor', 'temp', 'brewery', 'fermenter']`
6. If all checks pass → Device is detected! ✅

**Your ESP32 must pass ALL these checks to be found.**
