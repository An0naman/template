/**
 * ESP32 Sensor Master Control Integration
 * ========================================
 * 
 * This firmware connects to the Sensor Master Control system and operates in two modes:
 * 
 * OFFLINE MODE (🔴): Standalone operation when master control is unavailable
 * ONLINE MODE (🟢): Full integration with master control for remote configuration
 * 
 * Hardware: ESP32-WROOM-32
 * Framework: Arduino
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include "WebSerial.h"
#include <vector>
#include <map>
#include "time.h"

// ============================================================================
// CONFIGURATION - CUSTOMIZE THESE VALUES
// ============================================================================

// WiFi Configuration
const char* WIFI_SSID = "SkyNet Mesh";
const char* WIFI_PASSWORD = "TQ7@aecA&^eAmG)";

// NTP Configuration
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 0;
const int   daylightOffset_sec = 3600;

// Master Control Configuration
String masterUrl = "http://192.168.68.110:5001";  // Default/Fallback URL
const char* MDNS_SERVICE_NAME = "sensor-master";  // Hostname to look for (sensor-master.local)
const int MASTER_PORT = 5001;
const char* SENSOR_ID = "esp32_fermentation_002";
const char* SENSOR_NAME = "Fermentation Chamber 2";
const char* SENSOR_TYPE = "esp32_fermentation";
const char* FIRMWARE_VERSION = "1.1.1";

// Default Firmware Script (Fallback)
const char* DEFAULT_FIRMWARE_SCRIPT = R"({
  "name": "TempRead",
  "version": "1.0.0",
  "description": "",
  "actions": [
    {
      "type": "read_temperature",
      "pin": 4,
      "alias": "Temp"
    },
    {
      "type": "log",
      "message": "{Temp}"
    },
    {
      "type": "gpio_write",
      "pin": 2,
      "value": "HIGH",
      "alias": "Len"
    },
    {
      "type": "delay",
      "ms": 1000
    }
  ]
})";

// Timing Configuration
unsigned long pollingInterval = 5000;         // Default: 5 seconds for faster feedback
unsigned long heartbeatInterval = 300000;     // Default: 5 minutes
unsigned long offlineRetryInterval = 10000;   // Default: 10 seconds (retry connection faster)

// Hardware Configuration
#define ONE_WIRE_BUS 4            // Pin for Dallas Temperature Sensor
#define RELAY_PIN 25              // Digital pin for relay control
#define STATUS_LED_PIN 2          // Built-in LED

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// Operating mode
enum OperatingMode {
    MODE_OFFLINE,
    MODE_ONLINE
};
OperatingMode currentMode = MODE_OFFLINE;

// Timing variables
unsigned long lastDataSend = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastConnectionAttempt = 0;
unsigned long lastScriptCheck = 0;
unsigned long lastScriptExecution = 0;

// Configuration variables
String dataEndpoint = "";
String configHash = "";
bool hasReceivedConfig = false;

// Script management variables
String currentScript = "";
String currentScriptVersion = "";
int currentScriptId = -1;
bool scriptRunning = false;
unsigned long scriptLedTimer = 0;
bool scriptLedState = false;
unsigned long scriptLedOnDuration = 2000;  // Default 2 seconds
unsigned long scriptLedOffDuration = 2000; // Default 2 seconds

// Active script document (global to avoid re-parsing)
// JsonDocument activeScriptDoc; // Removed to prevent memory issues

// JSON script execution state
// struct ScriptContext {
//     JsonArray commands;
//     int index;
// };
// std::vector<ScriptContext> scriptStack; // Removed

// Alias mapping for script execution
std::map<String, int> pinAliases;
std::map<String, String> aliasTypes;
// Pin state tracking for reliable readback
std::map<int, int> pinStates;
// Global variable storage for float values (e.g. battery voltage)
std::map<String, float> globalVariables;

unsigned long commandStartTime = 0;
unsigned long commandDelay = 0;
bool waitingForDelay = false;

// Sensor data structure
struct SensorData {
    float temperature;
    bool relayState;
    unsigned long timestamp;
};

// Preferences for persistent storage
Preferences preferences;

// Web Server for discovery
WebServer server(80);
WebSerialClass WebSerial;

// ============================================================================
// FUNCTION DECLARATIONS
// ============================================================================

// WiFi and Connection
void connectToWiFi();
bool discoverMaster();

// Offline Mode Functions
void useOfflineConfiguration();
void handleDataOffline(SensorData data);
bool sendDataToFallbackEndpoint(SensorData data);

// Online Mode Functions
bool registerWithMaster();
bool getConfigFromMaster();
bool sendHeartbeat();
bool sendDataToMaster(SensorData data);
void sendRemoteLog(String message, String level = "info");
void processCommands(JsonArray commands);
void reportCommandResult(int commandId, String result, String message);

// Script Management Functions
void reportScriptExecution();
void reportRunningVersion(String version, int scriptId);
void checkForScriptUpdates();
void executeLocalScript();
void extractAliases(JsonArray actions);

// Hardware Functions
void initializeSensors();
SensorData readSensorData();
void setTargetTemperature(float targetTemp);

// ============================================================================
// SETUP FUNCTION
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    WebSerial.println("\n\n");
    WebSerial.println("========================================");
    WebSerial.println("ESP32 Sensor Master Control");
    WebSerial.println("========================================");
    WebSerial.println("Sensor ID: " + String(SENSOR_ID));
    WebSerial.println("Firmware: v" + String(FIRMWARE_VERSION) + " (Built: " + __DATE__ + " " + __TIME__ + ")");
    WebSerial.println("========================================\n");
    
    // Initialize hardware
    initializeSensors();
    
    // Initialize preferences
    preferences.begin("sensor-config", false);
    
    // Load saved script from preferences
    currentScript = preferences.getString("current_script", "");
    currentScriptVersion = preferences.getString("script_version", "");
    currentScriptId = preferences.getInt("script_id", -1);
    
    if (currentScript.length() > 0) {
        WebSerial.println("📜 Loaded saved script:");
        WebSerial.println("  Version: " + currentScriptVersion);
        WebSerial.println("  Script ID: " + String(currentScriptId));
    } else {
        WebSerial.println("ℹ️ No saved script found, using firmware default");
        currentScript = DEFAULT_FIRMWARE_SCRIPT;
        currentScriptVersion = "1.0.0 (Default)";
        currentScriptId = -1;
    }
    
    // Force script execution check immediately in loop
    lastScriptExecution = millis() - pollingInterval;
    
    // Connect to WiFi
    connectToWiFi();
    
    // Initialize time
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

    // Try to discover master via mDNS
    if (WiFi.status() == WL_CONNECTED) {
        discoverMaster();
    }
    
    // Start Web Server for discovery
    if (WiFi.status() == WL_CONNECTED) {
        server.on("/", HTTP_GET, []() {
            String html = "<!DOCTYPE html><html><head>";
            html += "<title>" + String(SENSOR_NAME) + " - ESP32</title>";
            html += "<meta charset='UTF-8'>";
            html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
            html += "<style>";
            html += "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }";
            html += ".container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden; }";
            html += ".header { background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%); color: white; padding: 30px; text-align: center; }";
            html += ".header h1 { margin: 0; font-size: 2.5em; font-weight: 300; }";
            html += ".header h2 { margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.8; font-weight: normal; }";
            html += ".content { padding: 30px; }";
            html += ".sensor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }";
            html += ".sensor-card { background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #e9ecef; transition: transform 0.2s; }";
            html += ".sensor-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }";
            html += ".sensor-value { font-size: 2.5em; font-weight: bold; color: #2d3748; margin: 10px 0; }";
            html += ".sensor-label { color: #718096; font-size: 1em; margin-bottom: 5px; display: flex; align-items: center; }";
            html += ".sensor-icon { font-size: 1.5em; margin-right: 10px; }";
            html += ".status { padding: 15px, margin: 20px 0; border-radius: 8px; display: flex; align-items: center; }";
            html += ".status.good { background-color: #d4edda; color: #155724; border-left: 4px solid #28a745; }";
            html += ".status.warning { background-color: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }";
            html += ".status.error { background-color: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }";
            html += ".info-section { margin: 30px 0; padding: 25px; background: #f8f9fa; border-radius: 10px; border: 1px solid #e9ecef; }";
            html += ".info-section h3 { margin-top: 0; color: #2d3748; }";
            html += ".info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }";
            html += ".info-item { padding: 10px 0; border-bottom: 1px solid #e9ecef; }";
            html += ".info-item:last-child { border-bottom: none; }";
            html += ".info-label { font-weight: 600; color: #4a5568; }";
            html += ".info-value { color: #2d3748; margin-top: 5px; }";
            html += ".button-group { display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }";
            html += ".btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; text-decoration: none; display: inline-flex; align-items: center; transition: all 0.2s; }";
            html += ".btn-primary { background: #4a5568; color: white; }";
            html += ".btn-primary:hover { background: #2d3748; }";
            html += ".btn-secondary { background: #e2e8f0; color: #4a5568; }";
            html += ".btn-secondary:hover { background: #cbd5e0; }";
            html += "@media (max-width: 768px) { .button-group { flex-direction: column; } .sensor-grid { grid-template-columns: 1fr; } }";
            html += "</style>";
            html += "</head><body>";
            
            html += "<div class='container'>";
            html += "<div class='header'>";
            html += "<h1>" + String(SENSOR_NAME) + "</h1>";
            html += "<h2>ESP32 Sensor Node</h2>";
            html += "</div>";
            
            html += "<div class='content'>";
            
            // Status
            String statusClass = (currentMode == MODE_ONLINE) ? "good" : "warning";
            String statusIcon = (currentMode == MODE_ONLINE) ? "✅" : "⚠️";
            String statusText = (currentMode == MODE_ONLINE) ? "Online (Connected to Master)" : "Offline (Standalone)";
            
            html += "<div class='status " + statusClass + "'>";
            html += "<span style='font-size: 1.5em; margin-right: 10px;'>" + statusIcon + "</span>";
            html += "<span><strong>Status:</strong> " + statusText + "</span>";
            html += "</div>";
            
            // Sensor Data
            SensorData data = readSensorData();
            
            html += "<div class='sensor-grid'>";
            html += "<div class='sensor-card'>";
            html += "<div class='sensor-label'><span class='sensor-icon'>🌡️</span>Temperature</div>";
            html += "<div class='sensor-value'>" + String(data.temperature, 1) + "°C</div>";
            html += "</div>";
            
            html += "<div class='sensor-card'>";
            html += "<div class='sensor-label'><span class='sensor-icon'>🔌</span>Relay State</div>";
            html += "<div class='sensor-value'>" + String(data.relayState ? "ON" : "OFF") + "</div>";
            html += "</div>";
            
            html += "<div class='sensor-card'>";
            html += "<div class='sensor-label'><span class='sensor-icon'>⏱️</span>Uptime</div>";
            html += "<div class='sensor-value' style='font-size: 1.5em;'>" + String(millis() / 1000) + "s</div>";
            html += "</div>";
            html += "</div>";
            
            // Serial Monitor
            html += "<div class='info-section'>";
            html += "<h3>🖥️ Serial Monitor</h3>";
            html += "<div id='serialMonitor' style='background: #1a202c; color: #48bb78; padding: 15px; border-radius: 5px; font-family: monospace; height: 300px; overflow-y: auto; font-size: 0.9em; white-space: pre-wrap;'>Connecting...</div>";
            html += "<div class='button-group' style='margin-top: 10px;'>";
            html += "<button class='btn btn-secondary' onclick='clearSerial()'>🗑️ Clear</button>";
            html += "<button class='btn btn-secondary' onclick='toggleAutoScroll()' id='autoScrollBtn'>⬇️ Auto-scroll: ON</button>";
            html += "</div>";
            html += "</div>";

            // Device Info
            html += "<div class='info-section'>";
            html += "<h3>📊 Device Information</h3>";
            html += "<div class='info-grid'>";
            html += "<div class='info-item'><div class='info-label'>Device ID</div><div class='info-value'>" + String(SENSOR_ID) + "</div></div>";
            html += "<div class='info-item'><div class='info-label'>Type</div><div class='info-value'>" + String(SENSOR_TYPE) + "</div></div>";
            html += "<div class='info-item'><div class='info-label'>IP Address</div><div class='info-value'>" + WiFi.localIP().toString() + "</div></div>";
            html += "<div class='info-item'><div class='info-label'>Master URL</div><div class='info-value'>" + masterUrl + "</div></div>";
            html += "<div class='info-item'><div class='info-label'>Firmware</div><div class='info-value'>" + String(FIRMWARE_VERSION) + "</div></div>";
            html += "</div>";
            html += "</div>";
            
            html += "</div></div>";
            
            // Scripts
            html += "<script>";
            html += "let autoScroll = true;";
            html += "function toggleAutoScroll() { autoScroll = !autoScroll; document.getElementById('autoScrollBtn').innerText = '⬇️ Auto-scroll: ' + (autoScroll ? 'ON' : 'OFF'); }";
            html += "function clearSerial() { document.getElementById('serialMonitor').innerHTML = ''; }";
            html += "async function updateSerial() {";
            html += "  try {";
            html += "    const response = await fetch('/api/serial');";
            html += "    const logs = await response.json();";
            html += "    const monitor = document.getElementById('serialMonitor');";
            html += "    monitor.innerHTML = logs.join('<br>');";
            html += "    if (autoScroll) monitor.scrollTop = monitor.scrollHeight;";
            html += "  } catch (e) { console.error('Serial update failed', e); }";
            html += "}";
            html += "setInterval(updateSerial, 2000);";
            html += "</script>";
            html += "</body></html>";
            
            server.send(200, "text/html", html);
        });
        
        server.on("/api", HTTP_GET, []() {
            JsonDocument doc;
            doc["name"] = SENSOR_NAME;
            doc["id"] = SENSOR_ID;
            doc["type"] = SENSOR_TYPE;
            
            // Add current sensor data
            SensorData data = readSensorData();
            doc["temperature"] = data.temperature;
            doc["relay_state"] = data.relayState;
            
            // Add dynamic global variables (battery, etc.)
            for (auto const& [key, val] : globalVariables) {
                doc[key] = val;
            }
            
            String json;
            serializeJson(doc, json);
            server.send(200, "application/json", json);
        });
        
        server.on("/api/serial", HTTP_GET, []() {
            server.send(200, "application/json", WebSerial.getLogsJson());
        });
        
        server.begin();
        WebSerial.println("🌐 Web Server started for discovery");
    }
    
    // Try to register with master control
    if (WiFi.status() == WL_CONNECTED) {
        WebSerial.println("\n🌐 Attempting to register with master control...");
        if (registerWithMaster()) {
            currentMode = MODE_ONLINE;
            WebSerial.println("✅ ONLINE MODE - Connected to master control");
            sendRemoteLog("Device online: " + String(SENSOR_ID), "system");
            
            // Get initial configuration
            getConfigFromMaster();
            
            // Check for available scripts
            checkForScriptUpdates();
        } else {
            currentMode = MODE_OFFLINE;
            WebSerial.println("⚠️ OFFLINE MODE - Master control unavailable");
            useOfflineConfiguration();
        }
    } else {
        currentMode = MODE_OFFLINE;
        WebSerial.println("⚠️ OFFLINE MODE - No WiFi connection");
        useOfflineConfiguration();
    }
    
    Serial.println("\n🚀 System ready!\n");
    WebSerial.println("System ready!");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
    // Handle Web Server requests
    server.handleClient();

    unsigned long currentTime = millis();
    
    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        WebSerial.println("❌ WiFi disconnected! Attempting to reconnect...");
        connectToWiFi();
    }
    
    // Read sensor data at polling interval
    if (currentTime - lastDataSend >= pollingInterval) {
        lastDataSend = currentTime;
        
        SensorData data = readSensorData();
        
        // Send data based on operating mode
        if (currentMode == MODE_ONLINE) {
            if (!sendDataToMaster(data)) {
                WebSerial.println("⚠️ Failed to send data to master, switching to OFFLINE MODE");
                currentMode = MODE_OFFLINE;
                useOfflineConfiguration();
            }
        } else {
            handleDataOffline(data);
        }
    }
    
    // ONLINE MODE: Send heartbeat and check for commands
    if (currentMode == MODE_ONLINE && currentTime - lastHeartbeat >= heartbeatInterval) {
        lastHeartbeat = currentTime;
        
        if (!sendHeartbeat()) {
            WebSerial.println("⚠️ Heartbeat failed, switching to OFFLINE MODE");
            currentMode = MODE_OFFLINE;
            useOfflineConfiguration();
        }
    }
    
    // ONLINE MODE: Check for script updates periodically (every 30 seconds)
    if (currentMode == MODE_ONLINE && currentTime - lastScriptCheck >= 30000) {
        lastScriptCheck = currentTime;
        checkForScriptUpdates();
    }
    
    // Execute local script if available (runs every polling interval)
    if (currentScript.length() > 0 && currentTime - lastScriptExecution >= pollingInterval) {
        lastScriptExecution = currentTime;
        executeLocalScript();
    }
    
    // Handle legacy LED blinking if script is running in continuous mode
    if (scriptRunning) {
        unsigned long currentMillis = millis();
        if (scriptLedState) {
            // LED is ON, check if we need to turn it OFF
            if (currentMillis - scriptLedTimer >= scriptLedOnDuration) {
                scriptLedState = false;
                scriptLedTimer = currentMillis;
                digitalWrite(2, LOW); 
            }
        } else {
            // LED is OFF, check if we need to turn it ON
            if (currentMillis - scriptLedTimer >= scriptLedOffDuration) {
                scriptLedState = true;
                scriptLedTimer = currentMillis;
                digitalWrite(2, HIGH); 
            }
        }
    }
    
    // OFFLINE MODE: Retry connection to master
    if (currentMode == MODE_OFFLINE && currentTime - lastConnectionAttempt >= offlineRetryInterval) {
        lastConnectionAttempt = currentTime;
        
        WebSerial.println("\n🔄 Retrying master control connection...");
        
        // Try to discover master if we don't have a good connection
        // Note: This might block for a second or two
        if (discoverMaster()) {
             if (registerWithMaster()) {
                currentMode = MODE_ONLINE;
                WebSerial.println("✅ Switched to ONLINE MODE");
                sendRemoteLog("Device reconnected: " + String(SENSOR_ID), "system");
                getConfigFromMaster();
                checkForScriptUpdates();
            }
        } else {
            // If discovery fails, try direct registration if URL is known
            if (masterUrl.length() > 0 && registerWithMaster()) {
                currentMode = MODE_ONLINE;
                WebSerial.println("✅ Switched to ONLINE MODE (Direct Connect)");
                sendRemoteLog("Device reconnected (Direct): " + String(SENSOR_ID), "system");
                getConfigFromMaster();
                checkForScriptUpdates();
            } else {
                WebSerial.println("⚠️ Still in OFFLINE MODE");
            }
        }
    }
    
    delay(100);  // Small delay to prevent tight loop
}

// ============================================================================
// SECTION 1: OFFLINE MODE FUNCTIONS
// ============================================================================
// CUSTOMIZE THIS SECTION FOR YOUR OFFLINE BEHAVIOR

void useOfflineConfiguration() {
    WebSerial.println("\n📋 Using offline configuration");
    
    // Load saved configuration from preferences
    pollingInterval = preferences.getULong("pollingInterval", 5000);
    
    // Safety check: Ensure polling interval is at least 1 second
    if (pollingInterval < 1000) {
        WebSerial.println("  ⚠️ Invalid polling interval (" + String(pollingInterval) + "ms), resetting to 5s");
        pollingInterval = 5000;
    }

    dataEndpoint = preferences.getString("dataEndpoint", "");
    
    // If we have a masterUrl but no dataEndpoint, default it
    if ((dataEndpoint == "null" || dataEndpoint.length() == 0) && masterUrl.length() > 0) {
         dataEndpoint = masterUrl + "/api/sensor-master/data";
    }
    
    // Safety check: Ensure data endpoint is valid
    if (dataEndpoint == "null") {
        dataEndpoint = "";
    }
    
    WebSerial.println("  Polling Interval: " + String(pollingInterval / 1000) + "s");
    WebSerial.println("  Data Endpoint: " + (dataEndpoint.length() > 0 ? dataEndpoint : "None"));
}

void handleDataOffline(SensorData data) {
    WebSerial.println("\n📊 Handling data in OFFLINE MODE");
    WebSerial.println("  Temperature: " + String(data.temperature) + "°C");
    WebSerial.println("  Relay State: " + String(data.relayState ? "ON" : "OFF"));
    
    // ⚠️ CUSTOMIZE HERE: Choose your offline data handling strategy
    
    // Option 1: Save to SD card (requires SD card module)
    // saveToSDCard(data);
    
    // Option 2: Send to fallback endpoint
    if (dataEndpoint.length() > 0) {
        sendDataToFallbackEndpoint(data);
    }
    
    // Option 3: Just display locally
    WebSerial.println("  💾 Data logged locally");
}

bool sendDataToFallbackEndpoint(SensorData data) {
    if (WiFi.status() != WL_CONNECTED || dataEndpoint.length() == 0 || dataEndpoint == "null") {
        return false;
    }
    
    WiFiClient client;
    client.setTimeout(2000);
    HTTPClient http;
    http.setReuse(false);
    http.begin(client, dataEndpoint);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["temperature"] = data.temperature;
    doc["relay_state"] = data.relayState;
    doc["timestamp"] = data.timestamp;
    doc["mode"] = "offline";
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    http.end();
    
    if (httpCode == 200) {
        WebSerial.println("  ✅ Data sent to fallback endpoint");
        return true;
    }
    
    WebSerial.println("  ❌ Failed to send to fallback endpoint");
    return false;
}

// ============================================================================
// SECTION 2: ONLINE MODE FUNCTIONS
// ============================================================================
// These functions handle master control integration

bool registerWithMaster() {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/register";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    // Build registration payload
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["sensor_name"] = SENSOR_NAME;
    doc["sensor_type"] = SENSOR_TYPE;
    doc["hardware_info"] = "ESP32-WROOM-32";
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["ip_address"] = WiFi.localIP().toString();
    doc["mac_address"] = WiFi.macAddress();
    
    JsonArray capabilities = doc["capabilities"].to<JsonArray>();
    capabilities.add("temperature");
    capabilities.add("relay_control");
    capabilities.add("analog_read");
    capabilities.add("read_battery");
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    WebSerial.println("  Sending registration to: " + url);
    int httpCode = http.POST(jsonString);
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument responseDoc;
        deserializeJson(responseDoc, response);
        
        String status = responseDoc["status"];
        WebSerial.println("  ✅ Registration successful!");
        WebSerial.println("  Status: " + status);
        WebSerial.println("  Assigned Master: " + String(responseDoc["assigned_master"].as<const char*>()));
        
        // Update polling interval if provided
        if (responseDoc.containsKey("check_in_interval")) {
            unsigned long newInterval = responseDoc["check_in_interval"].as<unsigned long>() * 1000;
            if (newInterval >= 5000) {
                pollingInterval = newInterval;
                WebSerial.println("  ⏱️ Polling interval updated to: " + String(pollingInterval / 1000) + "s");
            }
        }
        
        http.end();
        return true;
    }
    
    WebSerial.println("  ❌ Registration failed (HTTP " + String(httpCode) + ")");
    http.end();
    return false;
}

bool getConfigFromMaster() {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/config/" + String(SENSOR_ID);
    http.begin(client, url);
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument doc;
        deserializeJson(doc, response);
        
        if (doc["config_available"]) {
            // Update configuration
            configHash = doc["config_hash"].as<String>();
            
            JsonObject config = doc["config"];
            
            // Check for check_in_interval in the root response first (from API update)
            if (doc.containsKey("check_in_interval")) {
                unsigned long newInterval = doc["check_in_interval"].as<unsigned long>() * 1000;
                if (newInterval >= 5000) {
                    pollingInterval = newInterval;
                }
            } 
            // Fallback to config object if not in root
            else if (config.containsKey("polling_interval")) {
                unsigned long newPollingInterval = config["polling_interval"].as<unsigned long>() * 1000;
                if (newPollingInterval >= 5000) {
                    pollingInterval = newPollingInterval;
                }
            }

            dataEndpoint = config["data_endpoint"].as<String>();
            if (dataEndpoint == "null" || dataEndpoint.length() == 0) {
                // Default to master data endpoint if none specified
                dataEndpoint = masterUrl + "/api/sensor-master/data";
            }
            
            // Save configuration to preferences
            preferences.putULong("pollingInterval", pollingInterval);
            preferences.putString("dataEndpoint", dataEndpoint);
            preferences.putString("configHash", configHash);
            
            hasReceivedConfig = true;
            
            WebSerial.println("\n📥 Configuration received from master:");
            WebSerial.println("  Polling Interval: " + String(pollingInterval / 1000) + "s");
            WebSerial.println("  Data Endpoint: " + dataEndpoint);
            WebSerial.println("  Config Hash: " + configHash);
            
            // Process any pending commands
            if (doc["commands"].is<JsonArray>()) {
                JsonArray commands = doc["commands"];
                if (commands.size() > 0) {
                    processCommands(commands);
                }
            }
            
            http.end();
            return true;
        }
    }
    
    WebSerial.println("  ⚠️ No configuration available from master");
    http.end();
    return false;
}

bool sendHeartbeat() {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/heartbeat";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["status"] = "online";
    
    JsonObject metrics = doc["metrics"].to<JsonObject>();
    metrics["uptime"] = millis() / 1000;
    metrics["free_memory"] = ESP.getFreeHeap();
    metrics["wifi_rssi"] = WiFi.RSSI();
    
    // Add sensor data to heartbeat
    SensorData sensorData = readSensorData();
    metrics["temperature"] = sensorData.temperature;
    metrics["relay_state"] = sensorData.relayState;

    // Add dynamic global variables (battery, etc.) to heartbeat metrics
    for (auto const& [key, val] : globalVariables) {
        metrics[key] = val;
    }
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument responseDoc;
        deserializeJson(responseDoc, response);
        
        WebSerial.println("\n💓 Heartbeat sent successfully");
        
        // Check for configuration updates
        if (responseDoc["config_updated"]) {
            WebSerial.println("  🔄 Configuration updated, fetching new config...");
            getConfigFromMaster();
        }
        
        // Process any pending commands
        if (responseDoc["commands"].is<JsonArray>()) {
            JsonArray commands = responseDoc["commands"];
            if (commands.size() > 0) {
                processCommands(commands);
            }
        }
        
        http.end();
        return true;
    }
    
    WebSerial.println("  ❌ Heartbeat failed (HTTP " + String(httpCode) + ")");
    http.end();
    return false;
}

bool sendDataToMaster(SensorData data) {
    if (WiFi.status() != WL_CONNECTED || dataEndpoint.length() == 0 || dataEndpoint == "null") {
        return false;
    }
    
    WiFiClient client;
    client.setTimeout(2000);
    HTTPClient http;
    http.setReuse(false);
    http.begin(client, dataEndpoint);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["temperature"] = data.temperature;
    doc["relay_state"] = data.relayState;
    doc["timestamp"] = data.timestamp;
    doc["mode"] = "online";
    doc["firmware_version"] = FIRMWARE_VERSION;

    // Add all dynamic global variables (e.g. battery, soil, etc.)
    for (auto const& [key, val] : globalVariables) {
        doc[key] = val;
    }
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode == 200 || httpCode == 201) {
        WebSerial.println("\n📤 Data sent to master:");
        WebSerial.println("  Temperature: " + String(data.temperature) + "°C");
        WebSerial.println("  Relay State: " + String(data.relayState ? "ON" : "OFF"));
        http.end();
        return true;
    }
    
    WebSerial.println("  ❌ Failed to send data (HTTP " + String(httpCode) + ")");
    http.end();
    return false;
}

void sendRemoteLog(String message, String level) {
    if (currentMode != MODE_ONLINE || WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/logs";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["message"] = message;
    doc["level"] = level;
    
    String payload;
    serializeJson(doc, payload);
    
    // Use a longer timeout to ensure delivery even if server is busy
    http.setTimeout(5000);
    
    int httpCode = http.POST(payload);
    // We don't print success to avoid recursive logging if we were logging about network
    if (httpCode != 200 && httpCode != 201) {
        WebSerial.println("  ❌ Failed to send remote log (HTTP " + String(httpCode) + ")");
    }
    http.end();
}

// ============================================================================
// SECTION 2.1: SCRIPT MANAGEMENT & REPORTING
// ============================================================================

// Forward declarations
float resolveValue(String key);
bool evaluateCondition(String left, String op, String right);
void executeActions(JsonArray actions);
void extractAliases(JsonArray actions);

void extractAliases(JsonArray actions) {
    for (JsonObject action : actions) {
        if (action.containsKey("alias") && action.containsKey("pin")) {
            String alias = action["alias"].as<String>();
            int pin = action["pin"].as<int>();
            String type = action["type"] | "";
            
            if (alias.length() > 0) {
                pinAliases[alias] = pin;
                aliasTypes[alias] = type;
            }
        }
        // Recurse
        if (action.containsKey("then")) extractAliases(action["then"].as<JsonArray>());
        if (action.containsKey("else")) extractAliases(action["else"].as<JsonArray>());
    }
}

float resolveValue(String key) {
    key.trim(); // Handle potential whitespace
    
    // Check for constants (case-insensitive)
    if (key.equalsIgnoreCase("HIGH")) return 1.0;
    if (key.equalsIgnoreCase("LOW")) return 0.0;
    if (key.equalsIgnoreCase("true")) return 1.0;
    if (key.equalsIgnoreCase("false")) return 0.0;

    // Check if it's a number
    if (key.length() == 0) return 0;
    if (isdigit(key[0]) || key[0] == '-') return key.toFloat();
    
    // Check for sensor variables
    if (key == "sensor.temp") {
        return readSensorData().temperature;
    } else if (key == "sensor.relay") {
        return readSensorData().relayState ? 1.0 : 0.0;
    } else if (key == "current_time") {
        // Returns time in HHMM format (e.g. 1430 for 14:30)
        struct tm timeinfo;
        if(!getLocalTime(&timeinfo)){
            return -1.0;
        }
        return (timeinfo.tm_hour * 100) + timeinfo.tm_min;
    }
    
    // Check for GPIO (format: gpio.12)
    if (key.startsWith("gpio.")) {
        int pin = key.substring(5).toInt();
        // pinMode(pin, INPUT); // Removed to prevent disrupting OUTPUT pins
        return digitalRead(pin);
    }

    // Check for Analog (format: analog.34)
    if (key.startsWith("analog.")) {
        int pin = key.substring(7).toInt();
        return analogRead(pin);
    }

    // Check global variables (e.g. battery voltage)
    if (globalVariables.count(key)) {
        return globalVariables[key];
    }

    // Check aliases
    if (pinAliases.count(key)) {
        int pin = pinAliases[key];
        String type = aliasTypes.count(key) ? aliasTypes[key] : "";

        // Special handling for OneWire bus pin or read_temperature block - return actual temperature
        if (pin == ONE_WIRE_BUS || type == "read_temperature") {
            sensors.requestTemperatures();
            float temp = sensors.getTempCByIndex(0);
            WebSerial.println("🔍 DEBUG: Alias '" + key + "' resolved to Temperature: " + String(temp));
            return temp;
        }

        // Check if we have a tracked state for this pin
        if (pinStates.count(pin)) {
            int val = pinStates[pin];
            WebSerial.println("🔍 DEBUG: Alias '" + key + "' (Pin " + String(pin) + ") read from TRACKER: " + String(val));
            return (float)val;
        }
        // Fallback to reading the pin directly
        WebSerial.println("⚠️ DEBUG: Alias '" + key + "' (Pin " + String(pin) + ") NOT in tracker, reading HARDWARE");
        int val = digitalRead(pin);
        WebSerial.println("🔍 DEBUG: Alias '" + key + "' (Pin " + String(pin) + ") read from HARDWARE: " + String(val));
        return (float)val;
    }
    
    // Debug unresolvable keys (ignore common defaults)
    if (key != "0" && key != "") {
        WebSerial.println("⚠️ DEBUG: resolveValue('" + key + "') failed to resolve, returning 0");
    }
    
    return 0; // Default
}

bool evaluateCondition(String leftStr, String op, String rightStr) {
    float left = resolveValue(leftStr);
    float right = resolveValue(rightStr);
    
    if (op == "==") return left == right;
    if (op == "!=") return left != right;
    if (op == ">") return left > right;
    if (op == "<") return left < right;
    if (op == ">=") return left >= right;
    if (op == "<=") return left <= right;
    
    return false;
}

void executeActions(JsonArray actions) {
    for (JsonObject action : actions) {
        String type = action["type"] | "";
        
        if (type == "if") {
            JsonObject condition = action["condition"];
            String left = condition["left"] | "0";
            String op = condition["operator"] | "==";
            String right = condition["right"] | "0";
            
            bool result = evaluateCondition(left, op, right);
            String logMsg = "❓ IF " + left + " " + op + " " + right + " (" + String(resolveValue(left)) + " vs " + String(resolveValue(right)) + ") -> " + String(result ? "TRUE" : "FALSE");
            WebSerial.println(logMsg);
            Serial.println(logMsg);
            
            if (result) {
                if (!action["then"].isNull()) {
                    WebSerial.println("  ➡️ Executing THEN block");
                    executeActions(action["then"]);
                }
            } else {
                if (!action["else"].isNull()) {
                    WebSerial.println("  ➡️ Executing ELSE block");
                    executeActions(action["else"]);
                }
            }
            
        } else if (type == "delay") {
            int ms = action["ms"] | 1000;
            WebSerial.println("⏱️ Delay: " + String(ms) + "ms");
            delay(ms);
            
        } else if (type == "gpio_write") {
            int pin = action["pin"].as<int>();
            String value = action["value"].as<String>();
            int pinVal = (value == "HIGH" ? HIGH : LOW);
            
            pinMode(pin, OUTPUT);
            digitalWrite(pin, pinVal);
            
            // Update tracked state
            pinStates[pin] = pinVal;
            WebSerial.println("🔍 DEBUG: Updated Pin " + String(pin) + " state to " + String(pinVal) + " (Value: " + value + ")");
            
            WebSerial.println("✓ GPIO Write: Pin " + String(pin) + " = " + value);
            
        } else if (type == "gpio_read") {
            int pin = action["pin"].as<int>();
            pinMode(pin, INPUT);
            int val = digitalRead(pin);
            
            // Update tracked state
            pinStates[pin] = val;
            
            WebSerial.println("✓ GPIO Read: Pin " + String(pin) + " = " + String(val));

        } else if (type == "analog_read") {
            int pin = action["pin"].as<int>();
            int val = analogRead(pin);
            
            // Update tracked state
            pinStates[pin] = val;
            
            WebSerial.println("✓ Analog Read: Pin " + String(pin) + " = " + String(val));

        } else if (type == "read_battery") {
            int pin = action["pin"].as<int>();
            float r1 = action["r1"] | 100000.0; // Top resistor (connected to Battery +)
            float r2 = action["r2"] | 100000.0; // Bottom resistor (connected to GND)
            float vref = action["vref"] | 3.3;  // Reference voltage (usually 3.3V for ESP32)
            String alias = action["alias"] | "battery";
            
            pinMode(pin, INPUT);
            
            // Take multiple samples for averaging to reduce fluctuation
            long sum = 0;
            const int samples = 10;
            for(int i=0; i<samples; i++) {
                sum += analogRead(pin);
                delay(10);
            }
            float raw = sum / (float)samples;
            
            // Voltage Divider Formula: Vout = Vin * (R2 / (R1 + R2))
            // Vin = Vout * ((R1 + R2) / R2)
            // Vout = (raw / 4095.0) * vref
            
            float voltage = (raw / 4095.0) * vref * ((r1 + r2) / r2);
            
            // Calculate Percentage (Linear approximation for LiPo 3.3V - 4.2V)
            float minV = action["min_v"] | 3.3;
            float maxV = action["max_v"] | 4.2;
            int pct = (int)((voltage - minV) / (maxV - minV) * 100);
            if (pct < 0) pct = 0;
            if (pct > 100) pct = 100;

            globalVariables[alias] = voltage;
            globalVariables[alias + "_pct"] = (float)pct;
            
            WebSerial.println("✓ Battery: " + String(voltage) + "V (" + String(pct) + "%)");
            
            if (raw == 0) {
                WebSerial.println("⚠️ Warning: Battery raw reading is 0. Check wiring/resistors.");
            }

        } else if (type == "log") {
            String message = action["message"] | "Log message";
            
            // Support for {variable} syntax in message
            int startIndex = message.indexOf("{");
            while (startIndex >= 0) {
                int endIndex = message.indexOf("}", startIndex);
                if (endIndex > startIndex) {
                    String key = message.substring(startIndex + 1, endIndex);
                    float val = resolveValue(key);
                    String valStr = String(val);
                    // Clean up float formatting (remove .00)
                    if (valStr.endsWith(".00")) valStr.remove(valStr.length() - 3);
                    
                    message = message.substring(0, startIndex) + valStr + message.substring(endIndex + 1);
                    
                    // Search for next placeholder
                    startIndex = message.indexOf("{", startIndex + valStr.length());
                } else {
                    break;
                }
            }

            if (!action["value"].isNull()) {
                String valKey = action["value"];
                float val = resolveValue(valKey);
                message += " [" + valKey + "=" + String(val) + "]";
            }
            WebSerial.println("📝 Log: " + message);
            sendRemoteLog(message);
            
        } else if (type == "set_relay") {
            bool state = action["state"] | false;
            digitalWrite(RELAY_PIN, state ? HIGH : LOW);
            WebSerial.println("✓ Relay: " + String(state ? "ON" : "OFF"));
            
        } else if (type == "read_temperature") {
            SensorData data = readSensorData();
            WebSerial.println("✓ Temperature: " + String(data.temperature) + "°C");
            
        } else if (type == "hibernate") {
            int duration = action["duration"] | 60;
            String unit = action["unit"] | "seconds";
            
            unsigned long long multiplier = 1000000ULL; // Default microseconds for seconds
            
            if (unit == "minutes") {
                multiplier *= 60;
            } else if (unit == "hours") {
                multiplier *= 3600;
            }
            
            String msg = "💤 Entering deep sleep for " + String(duration) + " " + unit;
            WebSerial.println(msg);
            Serial.println(msg);
            sendRemoteLog(msg, "system");
            
            // Give time for logs to send
            delay(1000);
            
            // Configure deep sleep
            esp_sleep_enable_timer_wakeup(duration * multiplier);
            esp_deep_sleep_start();
        }
    }
}

/**
 * Report to master that we just executed a script
 * This updates the "Running/Recent/Idle" status on the dashboard
 */
void reportScriptExecution() {
    if (currentMode != MODE_ONLINE || WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    WiFiClient client;
    client.setTimeout(2000);
    HTTPClient http;
    http.setReuse(false);
    String url = masterUrl + "/api/sensor-master/script-executed";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    
    String payload;
    serializeJson(doc, payload);
    
    int httpCode = http.POST(payload);
    if (httpCode == 200) {
        WebSerial.println("[SCRIPT] ✅ Execution reported to master");
        Serial.flush();
    } else {
        WebSerial.println("[SCRIPT] ❌ Failed to report execution (HTTP " + String(httpCode) + ")");
    }
    http.end();
}

/**
 * Report what script version we're currently running
 * This updates the "Running Version" column on the dashboard
 */
void reportRunningVersion(String version, int scriptId = -1) {
    if (currentMode != MODE_ONLINE || WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/report-version";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["script_version"] = version;
    if (scriptId > 0) {
        doc["script_id"] = scriptId;
    }
    
    String payload;
    serializeJson(doc, payload);
    
    int httpCode = http.POST(payload);
    if (httpCode == 200) {
        WebSerial.println("[VERSION] ✅ Reported version " + version + " to master");
    } else {
        WebSerial.println("[VERSION] ❌ Failed to report version (HTTP " + String(httpCode) + ")");
    }
    http.end();
}

/**
 * Check for script updates from master control
 * Downloads new scripts and reports the version
 */
void checkForScriptUpdates() {
    if (currentMode != MODE_ONLINE || WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    WebSerial.println("\n[SCRIPT] Checking for updates... (Heap: " + String(ESP.getFreeHeap()) + ")");
    Serial.flush();
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/script/" + String(SENSOR_ID);
    
    // WebSerial.println("[SCRIPT] Connecting to: " + url);
    
    http.setReuse(false);
    if (!http.begin(client, url)) {
        WebSerial.println("[SCRIPT] ❌ Failed to begin HTTP connection");
        return;
    }
    
    // WebSerial.println("[SCRIPT] Sending GET request...");
    int httpCode = http.GET();
    // WebSerial.println("[SCRIPT] GET finished, code: " + String(httpCode));
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, response);
        
        if (error) {
            WebSerial.println("[SCRIPT] ❌ Failed to parse response");
            http.end();
            return;
        }
        
        // Check if script is available
        if (doc["script_available"]) {
            String scriptContent = doc["script"] | "";
            String scriptVersion = doc["version"] | "1.0.0";
            int scriptId = doc["id"] | -1;
            String scriptName = doc["name"] | "Unnamed Script";
            
            WebSerial.println("[SCRIPT] 📥 New script available:");
            WebSerial.println("  Name: " + scriptName);
            WebSerial.println("  Version: " + scriptVersion);
            WebSerial.println("  Script ID: " + String(scriptId));
            WebSerial.println("  Script content received (first 200 chars): " + scriptContent.substring(0, min(200, (int)scriptContent.length())));
            
            // Check if the script field is a JSON object (not a string)
            if (doc["script"].is<JsonObject>()) {
                WebSerial.println("  ⚠️ Script is a JSON object, converting to string");
                serializeJson(doc["script"], scriptContent);
                WebSerial.println("  Converted script: " + scriptContent);
            }
            
            // If script content is a stringified JSON, try to parse it to get the actual name/version
            if (scriptContent.length() > 0 && scriptContent.charAt(0) == '{') {
                JsonDocument innerDoc;
                DeserializationError innerError = deserializeJson(innerDoc, scriptContent);
                if (!innerError) {
                    // Extract name and version from the actual script content
                    String innerName = innerDoc["name"] | "";
                    String innerVersion = innerDoc["version"] | "";
                    if (innerName.length() > 0) {
                        scriptName = innerName;
                        WebSerial.println("  ✅ Found script name in content: " + scriptName);
                    }
                    if (innerVersion.length() > 0 && scriptVersion == "1.0.0") {
                        scriptVersion = innerVersion;
                        WebSerial.println("  ✅ Found version in content: " + scriptVersion);
                    }
                }
            }
            
            // Check if script has changed
            bool scriptChanged = (scriptContent != currentScript);

            // Save script to preferences
            preferences.putString("current_script", scriptContent);
            preferences.putString("script_version", scriptVersion);
            preferences.putInt("script_id", scriptId);
            
            // Update current script variables
            currentScript = scriptContent;
            currentScriptVersion = scriptVersion;
            currentScriptId = scriptId;
            
            // Report the version we just downloaded
            reportRunningVersion(scriptVersion, scriptId);
            
            WebSerial.println("[SCRIPT] ✅ Script updated and version reported");
            
            // Execute immediately
            if (scriptChanged) {
                WebSerial.println("[SCRIPT] 🔄 Script changed, restarting execution...");
                scriptRunning = false;
            }
            executeLocalScript();
        } else {
            WebSerial.println("[SCRIPT] ℹ️ No script assigned");
        }
    } else if (httpCode == 404) {
        WebSerial.println("[SCRIPT] ℹ️ No script available for this sensor");
    } else {
        WebSerial.println("[SCRIPT] ❌ Failed to check for updates (HTTP " + String(httpCode) + ")");
    }
    
    http.end();
}

/**
 * Execute the locally stored script
 * Reports execution to master after running
 */
void executeLocalScript() {
    if (currentScript.length() == 0) {
        return; // No script to execute
    }
    
    WebSerial.println("\n[SCRIPT] 🚀 Executing script...");
    WebSerial.println("  Version: " + currentScriptVersion);
    WebSerial.println("  Script ID: " + String(currentScriptId));
    
    // Parse script into local document
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, currentScript);
    
    if (error) {
        WebSerial.println("  ❌ JSON parse error: " + String(error.c_str()));
        return;
    }
    
    // Try both "actions" (new format) and "commands" (old format)
    JsonArray commandArray;
    if (doc["actions"].is<JsonArray>()) {
        commandArray = doc["actions"];
    } else if (doc["commands"].is<JsonArray>()) {
        commandArray = doc["commands"];
    }
    
    if (!commandArray.isNull() && commandArray.size() > 0) {
        // Build alias map first
        pinAliases.clear();
        aliasTypes.clear();
        pinStates.clear(); // Clear states at start of script to ensure fresh reads
        extractAliases(commandArray);
        
        WebSerial.println("🔍 DEBUG: Extracted " + String(pinAliases.size()) + " aliases");
        for(auto const& item : pinAliases) {
             WebSerial.println("  Alias: '" + item.first + "' -> Pin " + String(item.second));
        }
        
        // Execute using the new recursive engine
        WebSerial.println("  Executing " + String(commandArray.size()) + " action(s)...");
        executeActions(commandArray);
        WebSerial.println("[SCRIPT] ✅ Execution completed");
        reportScriptExecution();
        return;
    } 
    
    // Legacy LED blink pattern support
    WebSerial.println("  ⚠️ No JSON actions found, checking for legacy patterns...");
    
    // Check if script contains LED blink code
    if (currentScript.indexOf("LED") >= 0 || currentScript.indexOf("digitalWrite") >= 0) {
        if (!scriptRunning) {
            WebSerial.println("  ✅ Starting continuous LED control script");
            
            // Parse delay values from script
            int onDelayIdx = currentScript.indexOf("digitalWrite(LED_PIN, HIGH);");
            int offDelayIdx = currentScript.indexOf("digitalWrite(LED_PIN, LOW);");
            
            // Extract ON duration
            if (onDelayIdx >= 0) {
                int delayStart = currentScript.indexOf("delay(", onDelayIdx);
                if (delayStart >= 0) {
                    delayStart += 6; // Skip "delay("
                    int delayEnd = currentScript.indexOf(")", delayStart);
                    String delayStr = currentScript.substring(delayStart, delayEnd);
                    scriptLedOnDuration = delayStr.toInt();
                }
            }
            
            // Extract OFF duration
            if (offDelayIdx >= 0) {
                int delayStart = currentScript.indexOf("delay(", offDelayIdx);
                if (delayStart >= 0) {
                    delayStart += 6; // Skip "delay("
                    int delayEnd = currentScript.indexOf(")", delayStart);
                    String delayStr = currentScript.substring(delayStart, delayEnd);
                    scriptLedOffDuration = delayStr.toInt();
                }
            }
            
            WebSerial.println("  LED ON duration: " + String(scriptLedOnDuration) + "ms");
            WebSerial.println("  LED OFF duration: " + String(scriptLedOffDuration) + "ms");
            
            const int LED_PIN = 2;
            pinMode(LED_PIN, OUTPUT);
            scriptRunning = true;
            scriptLedTimer = millis();
            scriptLedState = false;
            
            // Report execution to master only when script starts
            WebSerial.println("[SCRIPT] ✅ Script started (continuous mode)");
            reportScriptExecution();
        }
    } else {
        WebSerial.println("  ⚠️ No executable pattern recognized");
    }
}

void processCommands(JsonArray commands) {
    WebSerial.println("\n📨 Processing " + String(commands.size()) + " command(s)");
    
    for (JsonVariant v : commands) {
        JsonObject cmd = v.as<JsonObject>();
        String commandType = cmd["command_type"];
        int commandId = cmd["id"];
        
        WebSerial.println("  Command ID: " + String(commandId));
        WebSerial.println("  Type: " + commandType);
        
        String result = "success";
        String message = "";
        
        // Execute command based on type
        if (commandType == "restart") {
            message = "Restarting device...";
            WebSerial.println("  🔄 " + message);
            // Report result before restarting
            reportCommandResult(commandId, result, message);
            delay(1000);
            ESP.restart();
            
        } else if (commandType == "update_config") {
            message = "Fetching new configuration";
            WebSerial.println("  ⚙️ " + message);
            getConfigFromMaster();
            
        } else if (commandType == "set_temperature") {
            float targetTemp = cmd["parameters"]["target_temperature"];
            message = "Target temperature set to " + String(targetTemp) + "°C";
            WebSerial.println("  🌡️ " + message);
            setTargetTemperature(targetTemp);
            
        } else if (commandType == "relay_control") {
            bool relayState = cmd["parameters"]["state"];
            message = "Relay turned " + String(relayState ? "ON" : "OFF");
            WebSerial.println("  🔌 " + message);
            digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
            
        } else {
            result = "error";
            message = "Unknown command type: " + commandType;
            WebSerial.println("  ❌ " + message);
        }
        
        // Report command execution result
        reportCommandResult(commandId, result, message);
    }
}

void reportCommandResult(int commandId, String result, String message) {
    if (WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    WiFiClient client;
    client.setTimeout(3000);
    HTTPClient http;
    String url = masterUrl + "/api/sensor-master/heartbeat";
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["status"] = "online";
    
    JsonArray results = doc["command_results"].to<JsonArray>();
    JsonObject cmdResult = results.add<JsonObject>();
    cmdResult["command_id"] = commandId;
    cmdResult["result"] = result;
    cmdResult["message"] = message;
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    http.POST(jsonString);
    http.end();
}

// ============================================================================
// SECTION 3: HARDWARE & SENSOR FUNCTIONS
// ============================================================================
// CUSTOMIZE THIS SECTION FOR YOUR HARDWARE

void initializeSensors() {
    Serial.println("DEBUG: Entering initializeSensors"); Serial.flush();
    // WebSerial.println("🔧 Initializing hardware...");
    Serial.println("🔧 Initializing hardware..."); Serial.flush();
    
    // Configure pins
    pinMode(STATUS_LED_PIN, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
    
    // Initialize Dallas Temperature Sensor
    sensors.begin();
    
    // Retry logic for sensor detection
    int retryCount = 0;
    int deviceCount = 0;
    while (deviceCount == 0 && retryCount < 5) {
        deviceCount = sensors.getDeviceCount();
        if (deviceCount == 0) {
            Serial.println("⚠️ No sensors found, retrying...");
            delay(250);
            sensors.begin();
            retryCount++;
        }
    }
    
    Serial.print("DEBUG: Found ");
    Serial.print(deviceCount);
    Serial.println(" DS18B20 sensors on bus.");
    WebSerial.println("DEBUG: Found " + String(deviceCount) + " DS18B20 sensors on bus.");
    
    // Initial states
    digitalWrite(STATUS_LED_PIN, LOW);
    digitalWrite(RELAY_PIN, LOW);
    
    // WebSerial.println("  ✅ Hardware initialized");
    Serial.println("  ✅ Hardware initialized"); Serial.flush();
}

SensorData readSensorData() {
    SensorData data;
    
    // Read temperature from Dallas sensor
    sensors.requestTemperatures(); 
    float temp = sensors.getTempCByIndex(0);
    
    // Check for error and retry once
    if (temp == -127.0 || temp == 85.0) {
        Serial.println("⚠️ Invalid reading (" + String(temp) + "), retrying...");
        sensors.begin(); // Re-init bus
        delay(200);
        sensors.requestTemperatures();
        temp = sensors.getTempCByIndex(0);
    }
    
    data.temperature = temp;
    
    // Read relay state
    data.relayState = digitalRead(RELAY_PIN);
    
    // Timestamp
    data.timestamp = millis();
    
    // Blink LED to show activity
    // digitalWrite(STATUS_LED_PIN, HIGH);
    // delay(50);
    // digitalWrite(STATUS_LED_PIN, LOW);
    
    // Serial Plotter Support
    Serial.print("Temperature:");
    Serial.print(data.temperature);
    Serial.print(",");
    Serial.print("Relay:");
    Serial.println(data.relayState ? 100 : 0); // Scale relay for visibility
    
    return data;
}

void setTargetTemperature(float targetTemp) {
    // ⚠️ CUSTOMIZE HERE: Implement your temperature control logic
    
    // Example: Simple on/off control
    SensorData data = readSensorData();
    
    if (data.temperature < targetTemp - 1.0) {
        // Too cold, turn on heater
        digitalWrite(RELAY_PIN, HIGH);
    } else if (data.temperature > targetTemp + 1.0) {
        // Too hot, turn off heater
        digitalWrite(RELAY_PIN, LOW);
    }
    
    // Save target temperature to preferences
    preferences.putFloat("targetTemp", targetTemp);
}

// ============================================================================
// SECTION 4: UTILITY FUNCTIONS
// ============================================================================

bool discoverMaster() {
    WebSerial.println("🔍 Looking for Master Control via mDNS...");
    
    if (!MDNS.begin(SENSOR_ID)) {
        WebSerial.println("  ❌ Error setting up mDNS responder!");
        return false;
    }
    
    WebSerial.println("  mDNS responder started. Searching for service: " + String(MDNS_SERVICE_NAME));
    
    // Query for the service
    // We look for _http._tcp
    int n = MDNS.queryService("http", "tcp");
    
    if (n == 0) {
        WebSerial.println("  ⚠️ No services found");
        return false;
    }
    
    WebSerial.println("  ✅ Found " + String(n) + " service(s)");
    
    for (int i = 0; i < n; ++i) {
        String hostname = MDNS.hostname(i);
        String serviceName = MDNS.txt(i, "type"); // We added 'type' property in Python
        
        WebSerial.println("  " + String(i + 1) + ": " + hostname + " (" + MDNS.IP(i).toString() + ":" + String(MDNS.port(i)) + ")");
        
        // Check if this is our master
        // In Python we set server name as "sensor-master.local."
        // MDNS.hostname(i) usually returns just "sensor-master"
        if (hostname.startsWith(MDNS_SERVICE_NAME) || serviceName == "sensor-master") {
            String ip = MDNS.IP(i).toString();
            int port = MDNS.port(i);
            
            // Validate IP address
            if (ip == "0.0.0.0" || ip == "127.0.0.1") {
                WebSerial.println("  ⚠️ Ignoring invalid discovered IP: " + ip);
                continue;
            }
            
            masterUrl = "http://" + ip + ":" + String(port);
            WebSerial.println("  🎯 Master Control found! URL updated to: " + masterUrl);
            return true;
        }
    }
    
    return false;
}

void connectToWiFi() {
    WebSerial.println("📡 Connecting to WiFi...");
    WebSerial.println("  SSID: " + String(WIFI_SSID));
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        WebSerial.println("  ✅ WiFi connected!");
        WebSerial.println("  IP Address: " + WiFi.localIP().toString());
        WebSerial.println("  Signal Strength: " + String(WiFi.RSSI()) + " dBm");
    } else {
        WebSerial.println("  ❌ WiFi connection failed!");
    }
}
