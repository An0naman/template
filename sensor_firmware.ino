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
#include <WebServer.h>

// ============================================================================
// CONFIGURATION - CUSTOMIZE THESE VALUES
// ============================================================================

// WiFi Configuration
const char* WIFI_SSID = "SkyNet Mesh";
const char* WIFI_PASSWORD = "TQ7@aecA&^eAmG)";

// Master Control Configuration
const char* MASTER_CONTROL_URL = "http://192.168.68.107:5001";  // Your Flask app URL
const char* SENSOR_ID = "esp32_fermentation_001";
const char* SENSOR_NAME = "Fermentation Chamber 1";
const char* SENSOR_TYPE = "esp32_fermentation";
const char* FIRMWARE_VERSION = "1.0.0";

// Timing Configuration
unsigned long pollingInterval = 60000;        // Default: 60 seconds
unsigned long heartbeatInterval = 300000;     // Default: 5 minutes
unsigned long offlineRetryInterval = 60000;   // Default: 1 minute (retry connection faster)

// Hardware Configuration
#define TEMP_SENSOR_PIN 34        // Analog pin for temperature sensor
#define RELAY_PIN 25              // Digital pin for relay control
#define STATUS_LED_PIN 2          // Built-in LED

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

// JSON script execution state
int currentCommandIndex = 0;
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

// ============================================================================
// FUNCTION DECLARATIONS
// ============================================================================

// WiFi and Connection
void connectToWiFi();

// Offline Mode Functions
void useOfflineConfiguration();
void handleDataOffline(SensorData data);
bool sendDataToFallbackEndpoint(SensorData data);

// Online Mode Functions
bool registerWithMaster();
bool getConfigFromMaster();
bool sendHeartbeat();
bool sendDataToMaster(SensorData data);
void processCommands(JsonArray commands);
void reportCommandResult(int commandId, String result, String message);

// Script Management Functions
void reportScriptExecution();
void reportRunningVersion(String version, int scriptId);
void checkForScriptUpdates();
void executeLocalScript();
void runJsonScriptContinuously();

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
    
    Serial.println("\n\n");
    Serial.println("========================================");
    Serial.println("ESP32 Sensor Master Control");
    Serial.println("========================================");
    Serial.println("Sensor ID: " + String(SENSOR_ID));
    Serial.println("Firmware: v" + String(FIRMWARE_VERSION));
    Serial.println("========================================\n");
    
    // Initialize hardware
    initializeSensors();
    
    // Initialize preferences
    preferences.begin("sensor-config", false);
    
    // Load saved script from preferences
    currentScript = preferences.getString("current_script", "");
    currentScriptVersion = preferences.getString("script_version", "");
    currentScriptId = preferences.getInt("script_id", -1);
    
    if (currentScript.length() > 0) {
        Serial.println("📜 Loaded saved script:");
        Serial.println("  Version: " + currentScriptVersion);
        Serial.println("  Script ID: " + String(currentScriptId));
    }
    
    // Connect to WiFi
    connectToWiFi();
    
    // Start Web Server for discovery
    if (WiFi.status() == WL_CONNECTED) {
        server.on("/", HTTP_GET, []() {
            String json = "{\"name\":\"" + String(SENSOR_NAME) + "\", \"id\":\"" + String(SENSOR_ID) + "\", \"type\":\"" + String(SENSOR_TYPE) + "\"}";
            server.send(200, "application/json", json);
        });
        server.on("/api", HTTP_GET, []() {
            String json = "{\"name\":\"" + String(SENSOR_NAME) + "\", \"id\":\"" + String(SENSOR_ID) + "\", \"type\":\"" + String(SENSOR_TYPE) + "\"}";
            server.send(200, "application/json", json);
        });
        server.begin();
        Serial.println("🌐 Web Server started for discovery");
    }
    
    // Try to register with master control
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n🌐 Attempting to register with master control...");
        if (registerWithMaster()) {
            currentMode = MODE_ONLINE;
            Serial.println("✅ ONLINE MODE - Connected to master control");
            
            // Get initial configuration
            getConfigFromMaster();
            
            // Check for available scripts
            checkForScriptUpdates();
        } else {
            currentMode = MODE_OFFLINE;
            Serial.println("⚠️ OFFLINE MODE - Master control unavailable");
            useOfflineConfiguration();
        }
    } else {
        currentMode = MODE_OFFLINE;
        Serial.println("⚠️ OFFLINE MODE - No WiFi connection");
        useOfflineConfiguration();
    }
    
    Serial.println("\n🚀 System ready!\n");
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
        Serial.println("❌ WiFi disconnected! Attempting to reconnect...");
        connectToWiFi();
    }
    
    // Read sensor data at polling interval
    if (currentTime - lastDataSend >= pollingInterval) {
        lastDataSend = currentTime;
        
        SensorData data = readSensorData();
        
        // Send data based on operating mode
        if (currentMode == MODE_ONLINE) {
            if (!sendDataToMaster(data)) {
                Serial.println("⚠️ Failed to send data to master, switching to OFFLINE MODE");
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
            Serial.println("⚠️ Heartbeat failed, switching to OFFLINE MODE");
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
    
    // Continuously run JSON script commands (non-blocking)
    if (scriptRunning) {
        runJsonScriptContinuously();
    }
    
    // OFFLINE MODE: Retry connection to master
    if (currentMode == MODE_OFFLINE && currentTime - lastConnectionAttempt >= offlineRetryInterval) {
        lastConnectionAttempt = currentTime;
        
        Serial.println("\n🔄 Retrying master control connection...");
        if (registerWithMaster()) {
            currentMode = MODE_ONLINE;
            Serial.println("✅ Switched to ONLINE MODE");
            getConfigFromMaster();
            checkForScriptUpdates();
        } else {
            Serial.println("⚠️ Still in OFFLINE MODE");
        }
    }
    
    delay(100);  // Small delay to prevent tight loop
}

// ============================================================================
// SECTION 1: OFFLINE MODE FUNCTIONS
// ============================================================================
// CUSTOMIZE THIS SECTION FOR YOUR OFFLINE BEHAVIOR

void useOfflineConfiguration() {
    Serial.println("\n📋 Using offline configuration");
    
    // Load saved configuration from preferences
    pollingInterval = preferences.getULong("pollingInterval", 60000);
    dataEndpoint = preferences.getString("dataEndpoint", "");
    
    Serial.println("  Polling Interval: " + String(pollingInterval / 1000) + "s");
    Serial.println("  Data Endpoint: " + (dataEndpoint.length() > 0 ? dataEndpoint : "None"));
}

void handleDataOffline(SensorData data) {
    Serial.println("\n📊 Handling data in OFFLINE MODE");
    Serial.println("  Temperature: " + String(data.temperature) + "°C");
    Serial.println("  Relay State: " + String(data.relayState ? "ON" : "OFF"));
    
    // ⚠️ CUSTOMIZE HERE: Choose your offline data handling strategy
    
    // Option 1: Save to SD card (requires SD card module)
    // saveToSDCard(data);
    
    // Option 2: Send to fallback endpoint
    if (dataEndpoint.length() > 0) {
        sendDataToFallbackEndpoint(data);
    }
    
    // Option 3: Just display locally
    Serial.println("  💾 Data logged locally");
}

bool sendDataToFallbackEndpoint(SensorData data) {
    if (WiFi.status() != WL_CONNECTED || dataEndpoint.length() == 0) {
        return false;
    }
    
    HTTPClient http;
    http.begin(dataEndpoint);
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
        Serial.println("  ✅ Data sent to fallback endpoint");
        return true;
    }
    
    Serial.println("  ❌ Failed to send to fallback endpoint");
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
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/register";
    http.begin(url);
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
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.println("  Sending registration to: " + url);
    int httpCode = http.POST(jsonString);
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument responseDoc;
        deserializeJson(responseDoc, response);
        
        String status = responseDoc["status"];
        Serial.println("  ✅ Registration successful!");
        Serial.println("  Status: " + status);
        Serial.println("  Assigned Master: " + String(responseDoc["assigned_master"].as<const char*>()));
        
        http.end();
        return true;
    }
    
    Serial.println("  ❌ Registration failed (HTTP " + String(httpCode) + ")");
    http.end();
    return false;
}

bool getConfigFromMaster() {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/config/" + String(SENSOR_ID);
    http.begin(url);
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument doc;
        deserializeJson(doc, response);
        
        if (doc["config_available"]) {
            // Update configuration
            configHash = doc["config_hash"].as<String>();
            
            JsonObject config = doc["config"];
            pollingInterval = config["polling_interval"].as<unsigned long>() * 1000;
            dataEndpoint = config["data_endpoint"].as<String>();
            
            // Save configuration to preferences
            preferences.putULong("pollingInterval", pollingInterval);
            preferences.putString("dataEndpoint", dataEndpoint);
            preferences.putString("configHash", configHash);
            
            hasReceivedConfig = true;
            
            Serial.println("\n📥 Configuration received from master:");
            Serial.println("  Polling Interval: " + String(pollingInterval / 1000) + "s");
            Serial.println("  Data Endpoint: " + dataEndpoint);
            Serial.println("  Config Hash: " + configHash);
            
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
    
    Serial.println("  ⚠️ No configuration available from master");
    http.end();
    return false;
}

bool sendHeartbeat() {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/heartbeat";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["status"] = "online";
    
    JsonObject metrics = doc["metrics"].to<JsonObject>();
    metrics["uptime"] = millis() / 1000;
    metrics["free_memory"] = ESP.getFreeHeap();
    metrics["wifi_rssi"] = WiFi.RSSI();
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument responseDoc;
        deserializeJson(responseDoc, response);
        
        Serial.println("\n💓 Heartbeat sent successfully");
        
        // Check for configuration updates
        if (responseDoc["config_updated"]) {
            Serial.println("  🔄 Configuration updated, fetching new config...");
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
    
    Serial.println("  ❌ Heartbeat failed (HTTP " + String(httpCode) + ")");
    http.end();
    return false;
}

bool sendDataToMaster(SensorData data) {
    if (WiFi.status() != WL_CONNECTED || dataEndpoint.length() == 0) {
        return false;
    }
    
    HTTPClient http;
    http.begin(dataEndpoint);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["temperature"] = data.temperature;
    doc["relay_state"] = data.relayState;
    doc["timestamp"] = data.timestamp;
    doc["mode"] = "online";
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode == 200 || httpCode == 201) {
        Serial.println("\n📤 Data sent to master:");
        Serial.println("  Temperature: " + String(data.temperature) + "°C");
        Serial.println("  Relay State: " + String(data.relayState ? "ON" : "OFF"));
        http.end();
        return true;
    }
    
    Serial.println("  ❌ Failed to send data (HTTP " + String(httpCode) + ")");
    http.end();
    return false;
}

// ============================================================================
// SECTION 2.1: SCRIPT MANAGEMENT & REPORTING
// ============================================================================

/**
 * Report to master that we just executed a script
 * This updates the "Running/Recent/Idle" status on the dashboard
 */
void reportScriptExecution() {
    if (currentMode != MODE_ONLINE || WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/script-executed";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    JsonDocument doc;
    doc["sensor_id"] = SENSOR_ID;
    
    String payload;
    serializeJson(doc, payload);
    
    int httpCode = http.POST(payload);
    if (httpCode == 200) {
        Serial.println("[SCRIPT] ✅ Execution reported to master");
    } else {
        Serial.println("[SCRIPT] ❌ Failed to report execution (HTTP " + String(httpCode) + ")");
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
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/report-version";
    http.begin(url);
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
        Serial.println("[VERSION] ✅ Reported version " + version + " to master");
    } else {
        Serial.println("[VERSION] ❌ Failed to report version (HTTP " + String(httpCode) + ")");
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
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/script/" + String(SENSOR_ID);
    http.begin(url);
    
    Serial.println("\n[SCRIPT] Checking for updates...");
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String response = http.getString();
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, response);
        
        if (error) {
            Serial.println("[SCRIPT] ❌ Failed to parse response");
            http.end();
            return;
        }
        
        // Check if script is available
        if (doc["script_available"]) {
            String scriptContent = doc["script"] | "";
            String scriptVersion = doc["version"] | "1.0.0";
            int scriptId = doc["id"] | -1;
            String scriptName = doc["name"] | "Unnamed Script";
            
            Serial.println("[SCRIPT] 📥 New script available:");
            Serial.println("  Name: " + scriptName);
            Serial.println("  Version: " + scriptVersion);
            Serial.println("  Script ID: " + String(scriptId));
            Serial.println("  Script content received (first 200 chars): " + scriptContent.substring(0, min(200, (int)scriptContent.length())));
            
            // Check if the script field is a JSON object (not a string)
            if (doc["script"].is<JsonObject>()) {
                Serial.println("  ⚠️ Script is a JSON object, converting to string");
                serializeJson(doc["script"], scriptContent);
                Serial.println("  Converted script: " + scriptContent);
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
                        Serial.println("  ✅ Found script name in content: " + scriptName);
                    }
                    if (innerVersion.length() > 0 && scriptVersion == "1.0.0") {
                        scriptVersion = innerVersion;
                        Serial.println("  ✅ Found version in content: " + scriptVersion);
                    }
                }
            }
            
            // Save script to preferences
            preferences.putString("current_script", scriptContent);
            preferences.putString("script_version", scriptVersion);
            preferences.putInt("script_id", scriptId);
            
            // Update current script variables
            currentScript = scriptContent;
            currentScriptVersion = scriptVersion;
            currentScriptId = scriptId;
            
            // Reset execution state for the new script
            scriptRunning = false;
            currentCommandIndex = 0;
            waitingForDelay = false;
            commandDelay = 0;
            
            // Trigger immediate execution
            executeLocalScript();
            
            // Report the version we just downloaded
            reportRunningVersion(scriptVersion, scriptId);
            
            Serial.println("[SCRIPT] ✅ Script updated and version reported");
        } else {
            Serial.println("[SCRIPT] ℹ️ No script assigned");
        }
    } else if (httpCode == 404) {
        Serial.println("[SCRIPT] ℹ️ No script available for this sensor");
    } else {
        Serial.println("[SCRIPT] ❌ Failed to check for updates (HTTP " + String(httpCode) + ")");
    }
    
    http.end();
}

/**
 * Run JSON script commands continuously (non-blocking)
 * Called from main loop when scriptRunning is true
 */
void runJsonScriptContinuously() {
    // Parse the current script
    JsonDocument scriptDoc;
    DeserializationError error = deserializeJson(scriptDoc, currentScript);
    
    if (error) {
        return; // Can't parse, skip
    }
    
    // Get the commands/actions array
    JsonArray commandArray;
    if (scriptDoc["actions"].is<JsonArray>()) {
        commandArray = scriptDoc["actions"];
    } else if (scriptDoc["commands"].is<JsonArray>()) {
        commandArray = scriptDoc["commands"];
    }
    
    if (commandArray.isNull() || commandArray.size() == 0) {
        scriptRunning = false;
        return; // No commands to execute
    }
    
    // Safety check: ensure index is within bounds
    if (currentCommandIndex >= commandArray.size()) {
        currentCommandIndex = 0;
        waitingForDelay = false;
    }
    
    // If we're waiting for a delay, check if it's time to continue
    if (waitingForDelay) {
        if (millis() - commandStartTime >= commandDelay) {
            waitingForDelay = false;
            currentCommandIndex++;
            
            // Loop back to start when we reach the end
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else {
            return; // Still waiting
        }
    }
    
    // Execute the current command
    if (currentCommandIndex < commandArray.size()) {
        JsonObject cmd = commandArray[currentCommandIndex].as<JsonObject>();
        String action = cmd["type"] | cmd["action"] | "";
        
        if (action == "delay") {
            // Start non-blocking delay
            int delayMs = cmd["ms"] | cmd["duration"] | 1000;
            commandDelay = delayMs;
            commandStartTime = millis();
            waitingForDelay = true;
        } else if (action == "gpio_write") {
            int pin = cmd["pin"] | 2;
            String valueStr = cmd["value"] | "";
            bool state = false;
            
            // Handle various ways to specify high/true
            if (valueStr == "HIGH" || valueStr == "high" || valueStr == "1" || valueStr == "true") {
                state = true;
            } else if (cmd["value"].is<bool>() && cmd["value"].as<bool>()) {
                state = true;
            } else if (cmd["state"].is<bool>()) {
                state = cmd["state"] | false;
            }
            
            pinMode(pin, OUTPUT);
            digitalWrite(pin, state ? HIGH : LOW);
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "gpio_read") {
            int pin = cmd["pin"] | 2;
            String mode = cmd["mode"] | "INPUT";
            
            // Set pin mode with pullup/pulldown support
            if (mode == "INPUT_PULLUP") {
                pinMode(pin, INPUT_PULLUP);
            } else if (mode == "INPUT_PULLDOWN") {
                pinMode(pin, INPUT_PULLDOWN);
            } else {
                pinMode(pin, INPUT);
            }
            
            int value = digitalRead(pin);
            Serial.println("[SCRIPT] GPIO" + String(pin) + " read: " + String(value) + " (mode: " + mode + ")");
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "analog_read") {
            int pin = cmd["pin"] | 34;
            int value = analogRead(pin);
            Serial.println("[SCRIPT] Analog pin " + String(pin) + ": " + String(value));
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "pwm_write") {
            int pin = cmd["pin"] | 2;
            int dutyCycle = cmd["duty"] | 128;  // 0-255
            int frequency = cmd["freq"] | 5000;  // Hz
            int channel = cmd["channel"] | 0;    // PWM channel 0-15
            
            // Configure PWM channel
            ledcSetup(channel, frequency, 8);  // 8-bit resolution
            ledcAttachPin(pin, channel);
            ledcWrite(channel, dutyCycle);
            
            Serial.println("[SCRIPT] PWM on GPIO" + String(pin) + ": " + String(dutyCycle) + " @ " + String(frequency) + "Hz");
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "analog_write") {
            // DAC output (only GPIO 25 and 26 on ESP32)
            int pin = cmd["pin"] | 25;
            int value = cmd["value"] | 128;  // 0-255
            
            if (pin == 25 || pin == 26) {
                dacWrite(pin, value);
                Serial.println("[SCRIPT] DAC on GPIO" + String(pin) + ": " + String(value));
            } else {
                Serial.println("[SCRIPT] ERROR: DAC only available on GPIO 25 or 26");
            }
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "read_temperature") {
            SensorData data = readSensorData();
            Serial.println("[SCRIPT] Temperature: " + String(data.temperature) + "°C");
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "set_relay") {
            bool state = cmd["state"] | false;
            digitalWrite(RELAY_PIN, state ? HIGH : LOW);
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else if (action == "log") {
            String message = cmd["message"] | "Log message";
            Serial.println("[SCRIPT] LOG: " + message);
            
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        } else {
            // Unknown command, skip it
            currentCommandIndex++;
            if (currentCommandIndex >= commandArray.size()) {
                currentCommandIndex = 0;
            }
        }
    }
}

/**
 * Execute the locally stored script
 * Reports execution to master after running
 */
void executeLocalScript() {
    if (currentScript.length() == 0) {
        return; // No script to execute
    }
    
    Serial.println("\n[SCRIPT] 🚀 Executing script...");
    Serial.println("  Version: " + currentScriptVersion);
    Serial.println("  Script ID: " + String(currentScriptId));
    Serial.println("  Script content: " + currentScript);
    
    // ⚠️ CUSTOMIZE HERE: Add your script execution logic
    // This is where you would parse and execute the script content
    // For example, if the script contains commands or logic for your sensor
    
    // Example: Parse script for simple commands
    // You might use a scripting engine or parse JSON commands
    JsonDocument scriptDoc;
    DeserializationError error = deserializeJson(scriptDoc, currentScript);
    Serial.println("  JSON parse error: " + String(error.c_str()));
    
    // Try both "actions" (new format) and "commands" (old format)
    JsonArray commandArray;
    if (!error && scriptDoc["actions"].is<JsonArray>()) {
        commandArray = scriptDoc["actions"];
    } else if (!error && scriptDoc["commands"].is<JsonArray>()) {
        commandArray = scriptDoc["commands"];
    }
    
    if (!commandArray.isNull() && commandArray.size() > 0) {
        // Start continuous JSON script execution
        if (!scriptRunning) {
            Serial.println("  Starting continuous JSON script execution with " + String(commandArray.size()) + " command(s)");
            scriptRunning = true;
            currentCommandIndex = 0;
            waitingForDelay = false;
            commandDelay = 0;
            reportScriptExecution();
        } else {
            Serial.println("  Script already running continuously");
        }
        return; // Don't execute LED pattern code
    } else {
        // If script is not JSON, look for LED control patterns
        Serial.println("  Executing custom script logic");
        
        // Check if script contains LED blink code
        if (currentScript.indexOf("LED") >= 0 || currentScript.indexOf("digitalWrite") >= 0) {
            if (!scriptRunning) {
                Serial.println("  ✅ Starting continuous LED control script");
                
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
                
                Serial.println("  LED ON duration: " + String(scriptLedOnDuration) + "ms");
                Serial.println("  LED OFF duration: " + String(scriptLedOffDuration) + "ms");
                
                const int LED_PIN = 2;
                pinMode(LED_PIN, OUTPUT);
                scriptRunning = true;
                scriptLedTimer = millis();
                scriptLedState = false;
                
                // Report execution to master only when script starts
                Serial.println("[SCRIPT] ✅ Script started (continuous mode)");
                reportScriptExecution();
            } else {
                Serial.println("  Script already running continuously");
            }
            // Script now runs continuously in loop()
        } else {
            // Generic script - just log it
            Serial.println("  Script content: " + currentScript.substring(0, 100) + "...");
            Serial.println("  ⚠️ No executable pattern recognized");
            Serial.println("[SCRIPT] ✅ Execution completed");
            reportScriptExecution();
        }
        return; // Don't report again for continuous scripts
    }
    
    // For JSON scripts, report after execution
    Serial.println("[SCRIPT] ✅ Execution completed");
    reportScriptExecution();
}

void processCommands(JsonArray commands) {
    Serial.println("\n📨 Processing " + String(commands.size()) + " command(s)");
    
    for (JsonVariant v : commands) {
        JsonObject cmd = v.as<JsonObject>();
        String commandType = cmd["command_type"];
        int commandId = cmd["id"];
        
        Serial.println("  Command ID: " + String(commandId));
        Serial.println("  Type: " + commandType);
        
        String result = "success";
        String message = "";
        
        // Execute command based on type
        if (commandType == "restart") {
            message = "Restarting device...";
            Serial.println("  🔄 " + message);
            // Report result before restarting
            reportCommandResult(commandId, result, message);
            delay(1000);
            ESP.restart();
            
        } else if (commandType == "update_config") {
            message = "Fetching new configuration";
            Serial.println("  ⚙️ " + message);
            getConfigFromMaster();
            
        } else if (commandType == "set_temperature") {
            float targetTemp = cmd["parameters"]["target_temperature"];
            message = "Target temperature set to " + String(targetTemp) + "°C";
            Serial.println("  🌡️ " + message);
            setTargetTemperature(targetTemp);
            
        } else if (commandType == "relay_control") {
            bool relayState = cmd["parameters"]["state"];
            message = "Relay turned " + String(relayState ? "ON" : "OFF");
            Serial.println("  🔌 " + message);
            digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
            
        } else {
            result = "error";
            message = "Unknown command type: " + commandType;
            Serial.println("  ❌ " + message);
        }
        
        // Report command execution result
        reportCommandResult(commandId, result, message);
    }
}

void reportCommandResult(int commandId, String result, String message) {
    if (WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    HTTPClient http;
    String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/heartbeat";
    http.begin(url);
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
    Serial.println("🔧 Initializing hardware...");
    
    // Configure pins
    pinMode(STATUS_LED_PIN, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
    pinMode(TEMP_SENSOR_PIN, INPUT);
    
    // Initial states
    digitalWrite(STATUS_LED_PIN, LOW);
    digitalWrite(RELAY_PIN, LOW);
    
    Serial.println("  ✅ Hardware initialized");
}

SensorData readSensorData() {
    SensorData data;
    
    // Read temperature from analog sensor
    // This is a simplified example - adjust for your actual sensor
    int rawValue = analogRead(TEMP_SENSOR_PIN);
    data.temperature = (rawValue / 4095.0) * 100.0;  // Convert to 0-100°C range
    
    // Read relay state
    data.relayState = digitalRead(RELAY_PIN);
    
    // Timestamp
    data.timestamp = millis();
    
    // Blink LED to show activity
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(50);
    digitalWrite(STATUS_LED_PIN, LOW);
    
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

void connectToWiFi() {
    Serial.println("📡 Connecting to WiFi...");
    Serial.println("  SSID: " + String(WIFI_SSID));
    
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
        Serial.println("  ✅ WiFi connected!");
        Serial.println("  IP Address: " + WiFi.localIP().toString());
        Serial.println("  Signal Strength: " + String(WiFi.RSSI()) + " dBm");
    } else {
        Serial.println("  ❌ WiFi connection failed!");
    }
}
