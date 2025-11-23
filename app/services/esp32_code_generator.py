# app/services/esp32_code_generator.py
"""
ESP32 Code Generator Service
=============================

This service generates ESP32 firmware code (Arduino C++ or MicroPython) that integrates
with the Sensor Master Control system. The generated code includes:

1. OFFLINE MODE: Standalone operation when master control is unavailable
2. ONLINE MODE: Full integration with master control for remote configuration

The code clearly separates these two modes so developers can customize each section
based on their needs.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ESP32CodeGenerator:
    """Generate ESP32 firmware code for sensor integration"""
    
    def __init__(self, db_connection):
        """
        Initialize the code generator with database connection
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.cursor = self.conn.cursor()
    
    def generate_code(self, sensor_id: str = None, sensor_type: str = None, 
                     language: str = "arduino", wifi_ssid: str = "", 
                     wifi_password: str = "", custom_config: Dict = None) -> Dict:
        """
        Generate ESP32 code based on sensor configuration
        
        Args:
            sensor_id: Existing sensor ID to generate code for
            sensor_type: Type of sensor if creating new sensor
            language: "arduino" or "micropython"
            wifi_ssid: WiFi SSID for the code
            wifi_password: WiFi password for the code
            custom_config: Optional custom configuration
            
        Returns:
            Dictionary with generated code and metadata
        """
        try:
            # Get sensor configuration
            config = self._get_sensor_config(sensor_id, sensor_type, custom_config)
            
            # Get master control URL
            master_url = self._get_master_url()
            
            # Generate code based on language
            if language.lower() == "arduino":
                code = self._generate_arduino_code(config, master_url, wifi_ssid, wifi_password)
            elif language.lower() == "micropython":
                code = self._generate_micropython_code(config, master_url, wifi_ssid, wifi_password)
            else:
                return {"error": f"Unsupported language: {language}"}
            
            return {
                "success": True,
                "code": code,
                "language": language,
                "sensor_id": config.get("sensor_id"),
                "sensor_type": config.get("sensor_type"),
                "generated_at": datetime.now().isoformat(),
                "configuration": config
            }
            
        except Exception as e:
            logger.error(f"Error generating ESP32 code: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _get_sensor_config(self, sensor_id: str = None, sensor_type: str = None, 
                          custom_config: Dict = None) -> Dict:
        """Get or create sensor configuration"""
        if custom_config:
            return custom_config
        
        if sensor_id:
            # Get existing sensor configuration
            self.cursor.execute('''
                SELECT sr.*, smc.api_endpoint, smc.instance_name
                FROM SensorRegistration sr
                LEFT JOIN SensorMasterControl smc ON sr.assigned_master_id = smc.id
                WHERE sr.sensor_id = ?
            ''', (sensor_id,))
            
            sensor = self.cursor.fetchone()
            if sensor:
                return {
                    "sensor_id": sensor['sensor_id'],
                    "sensor_type": sensor['sensor_type'],
                    "sensor_name": sensor.get('sensor_name', sensor['sensor_id']),
                    "master_url": sensor.get('api_endpoint', ''),
                    "hardware_info": sensor.get('hardware_info', 'ESP32'),
                    "firmware_version": sensor.get('firmware_version', '1.0.0')
                }
        
        # Generate default configuration
        return {
            "sensor_id": f"esp32_{sensor_type or 'sensor'}_{datetime.now().strftime('%Y%m%d')}",
            "sensor_type": sensor_type or "esp32_generic",
            "sensor_name": f"ESP32 Sensor",
            "master_url": "",
            "hardware_info": "ESP32-WROOM-32",
            "firmware_version": "1.0.0"
        }
    
    def _get_master_url(self) -> str:
        """Get the active master control URL"""
        try:
            self.cursor.execute('''
                SELECT api_endpoint FROM SensorMasterControl
                WHERE is_enabled = 1
                ORDER BY priority ASC
                LIMIT 1
            ''')
            result = self.cursor.fetchone()
            return result['api_endpoint'] if result else "http://localhost:5000"
        except:
            return "http://localhost:5000"
    
    def _generate_arduino_code(self, config: Dict, master_url: str, 
                               wifi_ssid: str, wifi_password: str) -> str:
        """Generate Arduino C++ code"""
        
        sensor_id = config.get("sensor_id", "esp32_sensor_001")
        sensor_type = config.get("sensor_type", "esp32_generic")
        sensor_name = config.get("sensor_name", "ESP32 Sensor")
        
        return f'''/*
 * ESP32 Sensor with Master Control Integration
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * Sensor ID: {sensor_id}
 * Sensor Type: {sensor_type}
 * 
 * This code includes two distinct operating modes:
 * 1. OFFLINE MODE - Runs when master control is unavailable
 * 2. ONLINE MODE - Runs when connected to master control
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>

// ============================================================================
// CONFIGURATION - Modify these values for your setup
// ============================================================================

const char* WIFI_SSID = "{wifi_ssid or 'YOUR_WIFI_SSID'}";
const char* WIFI_PASSWORD = "{wifi_password or 'YOUR_WIFI_PASSWORD'}";
const char* MASTER_CONTROL_URL = "{master_url}";
const char* SENSOR_ID = "{sensor_id}";
const char* SENSOR_TYPE = "{sensor_type}";
const char* SENSOR_NAME = "{sensor_name}";

// Timing configuration
const unsigned long CHECK_IN_INTERVAL = 300000;     // 5 minutes
const unsigned long DATA_SEND_INTERVAL = 60000;     // 1 minute (default)
const unsigned long CONNECTION_TIMEOUT = 10000;     // 10 seconds
const unsigned long MASTER_RETRY_INTERVAL = 600000; // 10 minutes

// ============================================================================
// GLOBAL STATE VARIABLES
// ============================================================================

enum OperatingMode {{
  MODE_OFFLINE,   // Operating without master control
  MODE_ONLINE     // Operating with master control
}};

OperatingMode currentMode = MODE_OFFLINE;
bool masterControlAvailable = false;
String dataEndpoint = "";
unsigned long pollingInterval = 60000;  // milliseconds
unsigned long lastCheckIn = 0;
unsigned long lastDataSend = 0;
unsigned long lastMasterRetry = 0;
unsigned long lastScriptCheck = 0;      // For script update checks

Preferences preferences;

// ============================================================================
// SETUP - INITIALIZATION
// ============================================================================

void setup() {{
  Serial.begin(115200);
  Serial.println("\\n\\n===========================================");
  Serial.println("ESP32 Sensor with Master Control");
  Serial.println("===========================================");
  Serial.println("Sensor ID: " + String(SENSOR_ID));
  Serial.println("Sensor Type: " + String(SENSOR_TYPE));
  Serial.println("===========================================\\n");
  
  // Initialize preferences (for persistent storage)
  preferences.begin("sensor", false);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Initialize sensor hardware
  initializeSensors();
  
  // Load any saved configuration
  loadSavedConfiguration();
  
  // Load saved script if available
  String savedScript = preferences.getString("current_script", "");
  if (savedScript.length() > 0) {{
    String scriptVersion = preferences.getString("script_version", "unknown");
    int scriptId = preferences.getInt("script_id", -1);
    Serial.println("[STARTUP] 📜 Found saved script:");
    Serial.println("  Version: " + scriptVersion);
    Serial.println("  Script ID: " + String(scriptId));
  }}
  
  // Attempt to register with master control
  Serial.println("\\n[STARTUP] Attempting to connect to master control...");
  if (registerWithMaster()) {{
    currentMode = MODE_ONLINE;
    Serial.println("[STARTUP] Master control connected - Running in ONLINE mode");
    getConfigFromMaster();
    
    // Check for script updates immediately after connecting
    checkForScriptUpdates();
  }} else {{
    currentMode = MODE_OFFLINE;
    Serial.println("[STARTUP] Master control unavailable - Running in OFFLINE mode");
    useOfflineConfiguration();
  }}
  
  Serial.println("\\n[STARTUP] Initialization complete\\n");
}}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {{
  unsigned long currentTime = millis();
  
  // Read sensor data
  SensorData data = readSensorData();
  
  // ========================================================================
  // DATA TRANSMISSION
  // ========================================================================
  if (currentTime - lastDataSend >= pollingInterval) {{
    
    if (currentMode == MODE_ONLINE) {{
      // ====================================================================
      // ONLINE MODE: Send data to master control endpoint
      // ====================================================================
      if (dataEndpoint.length() > 0) {{
        if (sendDataToMaster(data)) {{
          Serial.println("[ONLINE] Data sent to master successfully");
        }} else {{
          Serial.println("[ONLINE] Failed to send data to master");
          // Optionally fall back to offline mode on repeated failures
        }}
      }}
      
    }} else {{
      // ====================================================================
      // OFFLINE MODE: Handle data locally or send to fallback endpoint
      // ====================================================================
      handleDataOffline(data);
    }}
    
    lastDataSend = currentTime;
  }}
  
  // ========================================================================
  // MASTER CONTROL CHECK-IN (ONLINE MODE ONLY)
  // ========================================================================
  if (currentMode == MODE_ONLINE && currentTime - lastCheckIn >= CHECK_IN_INTERVAL) {{
    Serial.println("\\n[ONLINE] Performing check-in with master control...");
    
    // Send heartbeat
    if (sendHeartbeat()) {{
      Serial.println("[ONLINE] Heartbeat sent successfully");
      
      // Check for configuration updates
      getConfigFromMaster();
      
      // Check for script updates (every 30 seconds)
      if (currentTime - lastScriptCheck >= 30000) {{
        checkForScriptUpdates();
        lastScriptCheck = currentTime;
      }}
      
    }} else {{
      Serial.println("[ONLINE] Heartbeat failed - master may be unavailable");
      // Consider switching to offline mode after multiple failures
    }}
    
    lastCheckIn = currentTime;
  }}
  
  // ========================================================================
  // MASTER CONTROL RETRY (OFFLINE MODE ONLY)
  // ========================================================================
  if (currentMode == MODE_OFFLINE && currentTime - lastMasterRetry >= MASTER_RETRY_INTERVAL) {{
    Serial.println("\\n[OFFLINE] Retrying connection to master control...");
    
    if (registerWithMaster()) {{
      currentMode = MODE_ONLINE;
      Serial.println("[OFFLINE->ONLINE] Successfully connected to master control!");
      getConfigFromMaster();
    }} else {{
      Serial.println("[OFFLINE] Master still unavailable, continuing in offline mode");
    }}
    
    lastMasterRetry = currentTime;
  }}
  
  // Small delay to prevent overwhelming the system
  delay(100);
}}

// ============================================================================
// SECTION 1: OFFLINE MODE FUNCTIONS
// ============================================================================
// These functions run when the device cannot connect to master control
// Customize this section for standalone operation
// ============================================================================

void useOfflineConfiguration() {{
  Serial.println("\\n[OFFLINE MODE] Loading default configuration...");
  
  // Set default polling interval
  pollingInterval = 60000;  // 1 minute
  
  // Set fallback data endpoint (optional - can be empty for local-only operation)
  dataEndpoint = String(MASTER_CONTROL_URL) + "/api/devices/data";
  
  // Load any saved configuration from previous online session
  String savedEndpoint = preferences.getString("dataEndpoint", "");
  if (savedEndpoint.length() > 0) {{
    dataEndpoint = savedEndpoint;
    Serial.println("[OFFLINE MODE] Using saved endpoint: " + dataEndpoint);
  }}
  
  unsigned long savedInterval = preferences.getULong("pollingInterval", 0);
  if (savedInterval > 0) {{
    pollingInterval = savedInterval;
    Serial.println("[OFFLINE MODE] Using saved interval: " + String(pollingInterval/1000) + "s");
  }}
  
  Serial.println("[OFFLINE MODE] Configuration loaded");
  Serial.println("  - Polling Interval: " + String(pollingInterval/1000) + " seconds");
  Serial.println("  - Data Endpoint: " + (dataEndpoint.length() > 0 ? dataEndpoint : "None (local only)"));
}}

void handleDataOffline(SensorData data) {{
  Serial.println("\\n[OFFLINE MODE] Processing sensor data...");
  
  // ====================================================================
  // CUSTOMIZE THIS SECTION FOR YOUR OFFLINE BEHAVIOR
  // ====================================================================
  
  // Option 1: Log data locally to SD card or SPIFFS
  // saveDataLocally(data);
  
  // Option 2: Send to a hardcoded fallback endpoint
  if (dataEndpoint.length() > 0) {{
    if (sendDataToFallbackEndpoint(data)) {{
      Serial.println("[OFFLINE MODE] Data sent to fallback endpoint");
    }} else {{
      Serial.println("[OFFLINE MODE] Failed to send to fallback, storing locally");
      // Store for later transmission
    }}
  }} else {{
    Serial.println("[OFFLINE MODE] No endpoint configured, data logged only");
  }}
  
  // Option 3: Display on local screen or indicator
  // displayDataLocally(data);
  
  // Print data for debugging
  Serial.println("[OFFLINE MODE] Temperature: " + String(data.temperature) + "°C");
  Serial.println("[OFFLINE MODE] Target: " + String(data.targetTemp) + "°C");
  Serial.println("[OFFLINE MODE] Relay: " + String(data.relayState ? "ON" : "OFF"));
}}

bool sendDataToFallbackEndpoint(SensorData data) {{
  if (dataEndpoint.length() == 0) return false;
  
  HTTPClient http;
  http.begin(dataEndpoint);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(CONNECTION_TIMEOUT);
  
  StaticJsonDocument<512> doc;
  doc["device_id"] = SENSOR_ID;
  doc["timestamp"] = millis();
  doc["mode"] = "offline";  // Indicate this is from offline mode
  
  JsonObject sensor = doc.createNestedObject("sensor");
  sensor["temperature"] = data.temperature;
  sensor["target"] = data.targetTemp;
  sensor["valid"] = data.valid;
  
  JsonObject relay = doc.createNestedObject("relay");
  relay["state"] = data.relayState ? "on" : "off";
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  http.end();
  
  return (httpCode == 200 || httpCode == 201);
}}

// ============================================================================
// SECTION 2: ONLINE MODE FUNCTIONS
// ============================================================================
// These functions run when the device is connected to master control
// Master control provides configuration and receives data
// ============================================================================

bool registerWithMaster() {{
  if (String(MASTER_CONTROL_URL).length() == 0 || 
      String(MASTER_CONTROL_URL) == "YOUR_MASTER_URL") {{
    Serial.println("[REGISTRATION] No master control URL configured");
    return false;
  }}
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/register";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(CONNECTION_TIMEOUT);
  
  StaticJsonDocument<768> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["sensor_name"] = SENSOR_NAME;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["hardware_info"] = "ESP32-WROOM-32";
  doc["firmware_version"] = "1.0.0";
  doc["ip_address"] = WiFi.localIP().toString();
  doc["mac_address"] = WiFi.macAddress();
  
  JsonArray capabilities = doc.createNestedArray("capabilities");
  capabilities.add("temperature");
  capabilities.add("relay_control");
  capabilities.add("target_temperature");
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200 || httpCode == 201) {{
    String response = http.getString();
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error && responseDoc["status"] == "registered") {{
      masterControlAvailable = true;
      Serial.println("[REGISTRATION] Successfully registered with: " + 
                    String(responseDoc["assigned_master"].as<const char*>()));
      http.end();
      return true;
    }}
  }}
  
  Serial.println("[REGISTRATION] Failed with HTTP code: " + String(httpCode));
  masterControlAvailable = false;
  http.end();
  return false;
}}

bool getConfigFromMaster() {{
  if (!masterControlAvailable) return false;
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/config/" + String(SENSOR_ID);
  
  http.begin(url);
  http.setTimeout(CONNECTION_TIMEOUT);
  
  int httpCode = http.GET();
  
  if (httpCode == 200) {{
    String response = http.getString();
    StaticJsonDocument<2048> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error && doc["config_available"]) {{
      // Update configuration from master
      JsonObject config = doc["config"];
      
      unsigned long newInterval = config["polling_interval"] | 60;
      pollingInterval = newInterval * 1000;  // Convert to milliseconds
      
      const char* endpoint = config["data_endpoint"];
      if (endpoint) {{
        dataEndpoint = String(endpoint);
        
        // Save configuration for offline mode
        preferences.putString("dataEndpoint", dataEndpoint);
        preferences.putULong("pollingInterval", pollingInterval);
      }}
      
      Serial.println("[ONLINE MODE] Configuration updated:");
      Serial.println("  - Polling Interval: " + String(pollingInterval/1000) + "s");
      Serial.println("  - Data Endpoint: " + dataEndpoint);
      
      // Check for configuration changes
      if (doc["config_changed"]) {{
        Serial.println("[ONLINE MODE] Configuration has changed - applying updates");
        // Apply any sensor-specific configuration here
      }}
      
      // Process pending commands
      JsonArray commands = doc["commands"];
      if (commands.size() > 0) {{
        processCommands(commands);
      }}
      
      http.end();
      return true;
    }}
  }} else {{
    Serial.println("[ONLINE MODE] Failed to get config, HTTP code: " + String(httpCode));
  }}
  
  http.end();
  return false;
}}

bool sendHeartbeat() {{
  if (!masterControlAvailable) return false;
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/heartbeat";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(CONNECTION_TIMEOUT);
  
  StaticJsonDocument<512> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["status"] = "online";
  doc["ip_address"] = WiFi.localIP().toString();
  
  JsonObject metrics = doc.createNestedObject("metrics");
  metrics["uptime"] = millis() / 1000;
  metrics["free_memory"] = ESP.getFreeHeap();
  metrics["wifi_rssi"] = WiFi.RSSI();
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  http.end();
  
  return (httpCode == 200);
}}

bool sendDataToMaster(SensorData data) {{
  if (dataEndpoint.length() == 0) return false;
  
  HTTPClient http;
  http.begin(dataEndpoint);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(CONNECTION_TIMEOUT);
  
  StaticJsonDocument<512> doc;
  doc["device_id"] = SENSOR_ID;
  doc["timestamp"] = millis();
  doc["mode"] = "online";  // Indicate this is from online mode
  
  JsonObject sensor = doc.createNestedObject("sensor");
  sensor["temperature"] = data.temperature;
  sensor["target"] = data.targetTemp;
  sensor["valid"] = data.valid;
  
  JsonObject relay = doc.createNestedObject("relay");
  relay["state"] = data.relayState ? "on" : "off";
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  http.end();
  
  return (httpCode == 200 || httpCode == 201);
}}

void processCommands(JsonArray commands) {{
  Serial.println("\\n[ONLINE MODE] Processing " + String(commands.size()) + " command(s)...");
  
  for (JsonObject cmd : commands) {{
    String commandType = cmd["command_type"];
    int commandId = cmd["id"];
    
    Serial.println("[ONLINE MODE] Executing: " + commandType + " (ID: " + String(commandId) + ")");
    
    if (commandType == "update_config") {{
      // Re-fetch configuration
      getConfigFromMaster();
      
    }} else if (commandType == "restart") {{
      Serial.println("[ONLINE MODE] Restarting ESP32...");
      delay(1000);
      ESP.restart();
      
    }} else if (commandType == "set_target_temp") {{
      float newTarget = cmd["command_data"]["target"];
      setTargetTemperature(newTarget);
      Serial.println("[ONLINE MODE] Target temperature set to: " + String(newTarget));
      
    }} else if (commandType == "switch_to_offline") {{
      // Force offline mode for testing or maintenance
      currentMode = MODE_OFFLINE;
      masterControlAvailable = false;
      Serial.println("[ONLINE MODE] Switching to offline mode by command");
      
    }} else {{
      Serial.println("[ONLINE MODE] Unknown command type: " + commandType);
    }}
  }}
}}

// ============================================================================
// SECTION 3: HARDWARE & SENSOR FUNCTIONS
// ============================================================================
// Implement these functions based on your specific hardware setup
// ============================================================================

struct SensorData {{
  float temperature;
  float targetTemp;
  bool relayState;
  bool valid;
}};

void initializeSensors() {{
  Serial.println("[HARDWARE] Initializing sensors...");
  
  // ====================================================================
  // CUSTOMIZE THIS SECTION FOR YOUR HARDWARE
  // ====================================================================
  
  // Initialize temperature sensor (e.g., DS18B20, DHT22, etc.)
  // pinMode(TEMP_SENSOR_PIN, INPUT);
  
  // Initialize relay control
  // pinMode(RELAY_PIN, OUTPUT);
  // digitalWrite(RELAY_PIN, LOW);
  
  // Initialize any other sensors or actuators
  
  Serial.println("[HARDWARE] Sensors initialized");
}}

SensorData readSensorData() {{
  SensorData data;
  
  // ====================================================================
  // CUSTOMIZE THIS SECTION FOR YOUR HARDWARE
  // ====================================================================
  
  // Read temperature from your sensor
  data.temperature = 20.5;  // Replace with actual sensor reading
  
  // Get target temperature (from your control logic)
  data.targetTemp = 18.0;   // Replace with actual target
  
  // Get relay state
  data.relayState = false;  // Replace with actual relay state
  
  // Validate sensor reading
  data.valid = true;  // Set to false if sensor reading is invalid
  
  return data;
}}

void setTargetTemperature(float temp) {{
  // ====================================================================
  // CUSTOMIZE THIS SECTION FOR YOUR CONTROL LOGIC
  // ====================================================================
  
  Serial.println("[HARDWARE] Setting target temperature to: " + String(temp));
  // Implement your target temperature control logic here
}}

// ============================================================================
// SECTION 4: UTILITY FUNCTIONS
// ============================================================================

void connectToWiFi() {{
  Serial.println("[WIFI] Connecting to: " + String(WIFI_SSID));
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {{
    delay(500);
    Serial.print(".");
    attempts++;
  }}
  
  if (WiFi.status() == WL_CONNECTED) {{
    Serial.println("\\n[WIFI] Connected!");
    Serial.println("[WIFI] IP Address: " + WiFi.localIP().toString());
    Serial.println("[WIFI] MAC Address: " + WiFi.macAddress());
    Serial.println("[WIFI] RSSI: " + String(WiFi.RSSI()) + " dBm");
  }} else {{
    Serial.println("\\n[WIFI] Connection failed! Running in offline mode.");
  }}
}}

void loadSavedConfiguration() {{
  // Load any configuration saved from previous sessions
  Serial.println("[CONFIG] Loading saved configuration...");
  
  String savedEndpoint = preferences.getString("dataEndpoint", "");
  if (savedEndpoint.length() > 0) {{
    Serial.println("[CONFIG] Found saved endpoint: " + savedEndpoint);
  }}
  
  unsigned long savedInterval = preferences.getULong("pollingInterval", 0);
  if (savedInterval > 0) {{
    Serial.println("[CONFIG] Found saved interval: " + String(savedInterval/1000) + "s");
  }}
}}

// ============================================================================
// SECTION 5: JSON SCRIPT INTERPRETER
// ============================================================================
// Executes JSON command scripts downloaded from master control
// ============================================================================

void executeLocalScript(String jsonScript) {{
  Serial.println("[SCRIPT] 🚀 Executing JSON script...");
  
  if (jsonScript.length() == 0) {{
    Serial.println("[SCRIPT] ⚠️ No script content to execute");
    return;
  }}
  
  // Parse JSON
  StaticJsonDocument<2048> doc;
  DeserializationError error = deserializeJson(doc, jsonScript);
  
  if (error) {{
    Serial.println("[SCRIPT] ❌ Failed to parse JSON: " + String(error.c_str()));
    return;
  }}
  
  // Get script metadata
  String scriptName = doc["name"] | "Unnamed Script";
  String version = doc["version"] | "unknown";
  
  Serial.println("[SCRIPT] Name: " + scriptName);
  Serial.println("[SCRIPT] Version: " + version);
  
  // Get actions array
  JsonArray actions = doc["actions"];
  if (!actions) {{
    Serial.println("[SCRIPT] ⚠️ No actions found in script");
    return;
  }}
  
  Serial.println("[SCRIPT] Executing " + String(actions.size()) + " action(s)...");
  
  // Execute each action
  for (JsonObject action : actions) {{
    String type = action["type"] | "";
    
    if (type == "gpio_write") {{
      // GPIO Write: Set digital pin HIGH or LOW
      int pin = action["pin"] | 2;
      String value = action["value"] | "LOW";
      
      pinMode(pin, OUTPUT);
      digitalWrite(pin, value == "HIGH" ? HIGH : LOW);
      Serial.println("  ✓ GPIO Write: Pin " + String(pin) + " = " + value);
      
    }} else if (type == "gpio_read") {{
      // GPIO Read: Read digital pin state
      int pin = action["pin"] | 15;
      pinMode(pin, INPUT);
      int value = digitalRead(pin);
      Serial.println("  ✓ GPIO Read: Pin " + String(pin) + " = " + String(value));
      
    }} else if (type == "analog_read") {{
      // Analog Read: Read ADC value (0-4095 on ESP32)
      int pin = action["pin"] | 34;
      int value = analogRead(pin);
      Serial.println("  ✓ Analog Read: Pin " + String(pin) + " = " + String(value));
      
    }} else if (type == "read_temperature") {{
      // Read Temperature: Read from sensor
      SensorData data = readSensorData();
      Serial.println("  ✓ Temperature: " + String(data.temperature) + "°C");
      
    }} else if (type == "set_relay") {{
      // Set Relay: Control relay state
      bool state = action["state"] | false;
      // Implement your relay control here
      Serial.println("  ✓ Relay: " + String(state ? "ON" : "OFF"));
      
    }} else if (type == "delay") {{
      // Delay: Wait for specified milliseconds
      int ms = action["ms"] | 1000;
      Serial.println("  ⏱️ Delay: " + String(ms) + "ms");
      delay(ms);
      
    }} else if (type == "log") {{
      // Log: Print message to serial
      String message = action["message"] | "Log message";
      Serial.println("  📝 Log: " + message);
      
    }} else {{
      Serial.println("  ⚠️ Unknown action type: " + type);
    }}
  }}
  
  Serial.println("[SCRIPT] ✅ Script execution complete\\n");
}}

bool checkForScriptUpdates() {{
  if (String(MASTER_CONTROL_URL).length() == 0) return false;
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/script/" + String(SENSOR_ID);
  
  Serial.println("[SCRIPT] Checking for script updates...");
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {{
    String response = http.getString();
    StaticJsonDocument<4096> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error && doc["script_available"]) {{
      String newScript = doc["script"] | "";
      String scriptVersion = doc["version"] | "unknown";
      int scriptId = doc["script_id"] | -1;
      
      Serial.println("[SCRIPT] 📥 New script available:");
      Serial.println("  Version: " + scriptVersion);
      Serial.println("  Script ID: " + String(scriptId));
      
      // Save to preferences for persistence
      preferences.putString("current_script", newScript);
      preferences.putString("script_version", scriptVersion);
      preferences.putInt("script_id", scriptId);
      
      // Report version to master
      reportRunningVersion(scriptVersion, scriptId);
      
      Serial.println("[SCRIPT] ✅ Script downloaded and saved\\n");
      
      // Execute immediately
      executeLocalScript(newScript);
      
      http.end();
      return true;
    }}
  }}
  
  http.end();
  return false;
}}

void reportRunningVersion(String version, int scriptId) {{
  if (String(MASTER_CONTROL_URL).length() == 0) return;
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/report-version";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["version"] = version;
  if (scriptId > 0) doc["script_id"] = scriptId;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  if (httpCode == 200) {{
    Serial.println("[VERSION] ✅ Reported version to master: " + version);
  }}
  
  http.end();
}}

void reportScriptExecution(int scriptId) {{
  if (String(MASTER_CONTROL_URL).length() == 0) return;
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/script-executed";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["sensor_id"] = SENSOR_ID;
  if (scriptId > 0) doc["script_id"] = scriptId;
  
  String payload;
  serializeJson(doc, payload);
  
  http.POST(payload);
  http.end();
}}
'''
    
    def _generate_micropython_code(self, config: Dict, master_url: str, 
                                   wifi_ssid: str, wifi_password: str) -> str:
        """Generate MicroPython code"""
        
        sensor_id = config.get("sensor_id", "esp32_sensor_001")
        sensor_type = config.get("sensor_type", "esp32_generic")
        sensor_name = config.get("sensor_name", "ESP32 Sensor")
        
        return f'''"""
ESP32 Sensor with Master Control Integration (MicroPython)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Sensor ID: {sensor_id}
Sensor Type: {sensor_type}

This code includes two distinct operating modes:
1. OFFLINE MODE - Runs when master control is unavailable
2. ONLINE MODE - Runs when connected to master control
"""

import network
import urequests
import ujson
import time
import machine
from machine import Pin

# ============================================================================
# CONFIGURATION - Modify these values for your setup
# ============================================================================

WIFI_SSID = "{wifi_ssid or 'YOUR_WIFI_SSID'}"
WIFI_PASSWORD = "{wifi_password or 'YOUR_WIFI_PASSWORD'}"
MASTER_CONTROL_URL = "{master_url}"
SENSOR_ID = "{sensor_id}"
SENSOR_TYPE = "{sensor_type}"
SENSOR_NAME = "{sensor_name}"

# Timing configuration (in milliseconds)
CHECK_IN_INTERVAL = 300000      # 5 minutes
DATA_SEND_INTERVAL = 60000      # 1 minute (default)
CONNECTION_TIMEOUT = 10000      # 10 seconds
MASTER_RETRY_INTERVAL = 600000  # 10 minutes

# ============================================================================
# GLOBAL STATE VARIABLES
# ============================================================================

MODE_OFFLINE = 0
MODE_ONLINE = 1

current_mode = MODE_OFFLINE
master_control_available = False
data_endpoint = ""
polling_interval = 60000  # milliseconds
last_check_in = 0
last_data_send = 0
last_master_retry = 0

# ============================================================================
# SETUP - INITIALIZATION
# ============================================================================

def setup():
    """Initialize the sensor"""
    print("\\n\\n===========================================")
    print("ESP32 Sensor with Master Control")
    print("===========================================")
    print(f"Sensor ID: {{SENSOR_ID}}")
    print(f"Sensor Type: {{SENSOR_TYPE}}")
    print("===========================================\\n")
    
    global current_mode, last_check_in, last_data_send, last_master_retry
    
    # Connect to WiFi
    wlan = connect_wifi()
    
    if not wlan.isconnected():
        print("[STARTUP] WiFi not connected - Running in OFFLINE mode")
        current_mode = MODE_OFFLINE
        use_offline_configuration()
        return
    
    # Initialize sensors
    initialize_sensors()
    
    # Load saved configuration
    load_saved_configuration()
    
    # Attempt to register with master control
    print("\\n[STARTUP] Attempting to connect to master control...")
    if register_with_master():
        current_mode = MODE_ONLINE
        print("[STARTUP] Master control connected - Running in ONLINE mode")
        get_config_from_master()
    else:
        current_mode = MODE_OFFLINE
        print("[STARTUP] Master control unavailable - Running in OFFLINE mode")
        use_offline_configuration()
    
    print("\\n[STARTUP] Initialization complete\\n")
    
    # Initialize timing
    last_check_in = time.ticks_ms()
    last_data_send = time.ticks_ms()
    last_master_retry = time.ticks_ms()

# ============================================================================
# MAIN LOOP
# ============================================================================

def loop():
    """Main loop"""
    global last_check_in, last_data_send, last_master_retry, current_mode
    
    current_time = time.ticks_ms()
    
    # Read sensor data
    data = read_sensor_data()
    
    # ========================================================================
    # DATA TRANSMISSION
    # ========================================================================
    if time.ticks_diff(current_time, last_data_send) >= polling_interval:
        
        if current_mode == MODE_ONLINE:
            # ================================================================
            # ONLINE MODE: Send data to master control endpoint
            # ================================================================
            if data_endpoint:
                if send_data_to_master(data):
                    print("[ONLINE] Data sent to master successfully")
                else:
                    print("[ONLINE] Failed to send data to master")
        else:
            # ================================================================
            # OFFLINE MODE: Handle data locally or send to fallback endpoint
            # ================================================================
            handle_data_offline(data)
        
        last_data_send = current_time
    
    # ========================================================================
    # MASTER CONTROL CHECK-IN (ONLINE MODE ONLY)
    # ========================================================================
    if current_mode == MODE_ONLINE and time.ticks_diff(current_time, last_check_in) >= CHECK_IN_INTERVAL:
        print("\\n[ONLINE] Performing check-in with master control...")
        
        if send_heartbeat():
            print("[ONLINE] Heartbeat sent successfully")
            get_config_from_master()
        else:
            print("[ONLINE] Heartbeat failed - master may be unavailable")
        
        last_check_in = current_time
    
    # ========================================================================
    # MASTER CONTROL RETRY (OFFLINE MODE ONLY)
    # ========================================================================
    if current_mode == MODE_OFFLINE and time.ticks_diff(current_time, last_master_retry) >= MASTER_RETRY_INTERVAL:
        print("\\n[OFFLINE] Retrying connection to master control...")
        
        if register_with_master():
            current_mode = MODE_ONLINE
            print("[OFFLINE->ONLINE] Successfully connected to master control!")
            get_config_from_master()
        else:
            print("[OFFLINE] Master still unavailable, continuing in offline mode")
        
        last_master_retry = current_time
    
    time.sleep_ms(100)

# ============================================================================
# SECTION 1: OFFLINE MODE FUNCTIONS
# ============================================================================
# These functions run when the device cannot connect to master control
# Customize this section for standalone operation
# ============================================================================

def use_offline_configuration():
    """Load default offline configuration"""
    global polling_interval, data_endpoint
    
    print("\\n[OFFLINE MODE] Loading default configuration...")
    
    # Set default polling interval
    polling_interval = 60000  # 1 minute
    
    # Set fallback data endpoint (optional)
    data_endpoint = f"{{MASTER_CONTROL_URL}}/api/devices/data"
    
    # Try to load saved configuration
    try:
        with open('sensor_config.json', 'r') as f:
            config = ujson.load(f)
            if 'dataEndpoint' in config:
                data_endpoint = config['dataEndpoint']
                print(f"[OFFLINE MODE] Using saved endpoint: {{data_endpoint}}")
            if 'pollingInterval' in config:
                polling_interval = config['pollingInterval']
                print(f"[OFFLINE MODE] Using saved interval: {{polling_interval//1000}}s")
    except:
        pass
    
    print("[OFFLINE MODE] Configuration loaded")
    print(f"  - Polling Interval: {{polling_interval//1000}} seconds")
    print(f"  - Data Endpoint: {{data_endpoint if data_endpoint else 'None (local only)'}}")

def handle_data_offline(data):
    """Handle sensor data in offline mode"""
    print("\\n[OFFLINE MODE] Processing sensor data...")
    
    # ====================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR OFFLINE BEHAVIOR
    # ====================================================================
    
    # Option 1: Save data locally to file
    # save_data_locally(data)
    
    # Option 2: Send to fallback endpoint
    if data_endpoint:
        if send_data_to_fallback_endpoint(data):
            print("[OFFLINE MODE] Data sent to fallback endpoint")
        else:
            print("[OFFLINE MODE] Failed to send to fallback, storing locally")
    else:
        print("[OFFLINE MODE] No endpoint configured, data logged only")
    
    # Print data for debugging
    print(f"[OFFLINE MODE] Temperature: {{data['temperature']}}°C")
    print(f"[OFFLINE MODE] Target: {{data['target_temp']}}°C")
    print(f"[OFFLINE MODE] Relay: {{'ON' if data['relay_state'] else 'OFF'}}")

def send_data_to_fallback_endpoint(data):
    """Send data to fallback endpoint"""
    if not data_endpoint:
        return False
    
    try:
        payload = {{
            "device_id": SENSOR_ID,
            "timestamp": time.ticks_ms(),
            "mode": "offline",
            "sensor": {{
                "temperature": data['temperature'],
                "target": data['target_temp'],
                "valid": data['valid']
            }},
            "relay": {{
                "state": "on" if data['relay_state'] else "off"
            }}
        }}
        
        response = urequests.post(
            data_endpoint,
            json=payload,
            headers={{'Content-Type': 'application/json'}}
        )
        
        success = response.status_code in [200, 201]
        response.close()
        return success
        
    except Exception as e:
        print(f"[OFFLINE MODE] Error sending data: {{e}}")
        return False

# ============================================================================
# SECTION 2: ONLINE MODE FUNCTIONS
# ============================================================================
# These functions run when the device is connected to master control
# Master control provides configuration and receives data
# ============================================================================

def register_with_master():
    """Register sensor with master control"""
    global master_control_available
    
    if not MASTER_CONTROL_URL or MASTER_CONTROL_URL == "YOUR_MASTER_URL":
        print("[REGISTRATION] No master control URL configured")
        return False
    
    url = f"{{MASTER_CONTROL_URL}}/api/sensor-master/register"
    
    payload = {{
        "sensor_id": SENSOR_ID,
        "sensor_name": SENSOR_NAME,
        "sensor_type": SENSOR_TYPE,
        "hardware_info": "ESP32",
        "firmware_version": "1.0.0",
        "capabilities": ["temperature", "relay_control", "target_temperature"]
    }}
    
    try:
        response = urequests.post(
            url,
            json=payload,
            headers={{'Content-Type': 'application/json'}}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get('status') == 'registered':
                master_control_available = True
                print(f"[REGISTRATION] Successfully registered with: {{data.get('assigned_master')}}")
                response.close()
                return True
        
        print(f"[REGISTRATION] Failed with HTTP code: {{response.status_code}}")
        response.close()
        
    except Exception as e:
        print(f"[REGISTRATION] Error: {{e}}")
    
    master_control_available = False
    return False

def get_config_from_master():
    """Get configuration from master control"""
    global polling_interval, data_endpoint
    
    if not master_control_available:
        return False
    
    url = f"{{MASTER_CONTROL_URL}}/api/sensor-master/config/{{SENSOR_ID}}"
    
    try:
        response = urequests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('config_available'):
                config = data.get('config', {{}})
                
                new_interval = config.get('polling_interval', 60)
                polling_interval = new_interval * 1000  # Convert to milliseconds
                
                endpoint = config.get('data_endpoint')
                if endpoint:
                    data_endpoint = endpoint
                    
                    # Save configuration for offline mode
                    try:
                        with open('sensor_config.json', 'w') as f:
                            ujson.dump({{
                                'dataEndpoint': data_endpoint,
                                'pollingInterval': polling_interval
                            }}, f)
                    except:
                        pass
                
                print("[ONLINE MODE] Configuration updated:")
                print(f"  - Polling Interval: {{polling_interval//1000}}s")
                print(f"  - Data Endpoint: {{data_endpoint}}")
                
                if data.get('config_changed'):
                    print("[ONLINE MODE] Configuration has changed - applying updates")
                
                # Process pending commands
                commands = data.get('commands', [])
                if commands:
                    process_commands(commands)
                
                response.close()
                return True
        else:
            print(f"[ONLINE MODE] Failed to get config, HTTP code: {{response.status_code}}")
        
        response.close()
        
    except Exception as e:
        print(f"[ONLINE MODE] Error getting config: {{e}}")
    
    return False

def send_heartbeat():
    """Send heartbeat to master control"""
    if not master_control_available:
        return False
    
    url = f"{{MASTER_CONTROL_URL}}/api/sensor-master/heartbeat"
    
    payload = {{
        "sensor_id": SENSOR_ID,
        "status": "online",
        "metrics": {{
            "uptime": time.ticks_ms() // 1000,
            "free_memory": machine.mem_free()
        }}
    }}
    
    try:
        response = urequests.post(
            url,
            json=payload,
            headers={{'Content-Type': 'application/json'}}
        )
        
        success = response.status_code == 200
        response.close()
        return success
        
    except Exception as e:
        print(f"[ONLINE MODE] Heartbeat error: {{e}}")
        return False

def send_data_to_master(data):
    """Send sensor data to master control"""
    if not data_endpoint:
        return False
    
    try:
        payload = {{
            "device_id": SENSOR_ID,
            "timestamp": time.ticks_ms(),
            "mode": "online",
            "sensor": {{
                "temperature": data['temperature'],
                "target": data['target_temp'],
                "valid": data['valid']
            }},
            "relay": {{
                "state": "on" if data['relay_state'] else "off"
            }}
        }}
        
        response = urequests.post(
            data_endpoint,
            json=payload,
            headers={{'Content-Type': 'application/json'}}
        )
        
        success = response.status_code in [200, 201]
        response.close()
        return success
        
    except Exception as e:
        print(f"[ONLINE MODE] Error sending data: {{e}}")
        return False

def process_commands(commands):
    """Process commands from master control"""
    global current_mode, master_control_available
    
    print(f"\\n[ONLINE MODE] Processing {{len(commands)}} command(s)...")
    
    for cmd in commands:
        command_type = cmd.get('command_type')
        command_id = cmd.get('id')
        
        print(f"[ONLINE MODE] Executing: {{command_type}} (ID: {{command_id}})")
        
        if command_type == 'update_config':
            get_config_from_master()
            
        elif command_type == 'restart':
            print("[ONLINE MODE] Restarting ESP32...")
            time.sleep(1)
            machine.reset()
            
        elif command_type == 'set_target_temp':
            new_target = cmd.get('command_data', {{}}).get('target')
            set_target_temperature(new_target)
            print(f"[ONLINE MODE] Target temperature set to: {{new_target}}")
            
        elif command_type == 'switch_to_offline':
            current_mode = MODE_OFFLINE
            master_control_available = False
            print("[ONLINE MODE] Switching to offline mode by command")
            
        else:
            print(f"[ONLINE MODE] Unknown command type: {{command_type}}")

# ============================================================================
# SECTION 3: HARDWARE & SENSOR FUNCTIONS
# ============================================================================
# Implement these functions based on your specific hardware setup
# ============================================================================

def initialize_sensors():
    """Initialize sensor hardware"""
    print("[HARDWARE] Initializing sensors...")
    
    # ====================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR HARDWARE
    # ====================================================================
    
    # Initialize temperature sensor
    # global temp_sensor
    # temp_sensor = DS18X20(OneWire(Pin(4)))
    
    # Initialize relay
    # global relay_pin
    # relay_pin = Pin(2, Pin.OUT)
    # relay_pin.value(0)
    
    print("[HARDWARE] Sensors initialized")

def read_sensor_data():
    """Read data from sensors"""
    # ====================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR HARDWARE
    # ====================================================================
    
    data = {{
        'temperature': 20.5,  # Replace with actual sensor reading
        'target_temp': 18.0,   # Replace with actual target
        'relay_state': False,  # Replace with actual relay state
        'valid': True          # Set to False if sensor reading is invalid
    }}
    
    return data

def set_target_temperature(temp):
    """Set target temperature"""
    # ====================================================================
    # CUSTOMIZE THIS SECTION FOR YOUR CONTROL LOGIC
    # ====================================================================
    
    print(f"[HARDWARE] Setting target temperature to: {{temp}}")

# ============================================================================
# SECTION 4: UTILITY FUNCTIONS
# ============================================================================

def connect_wifi():
    """Connect to WiFi"""
    print(f"[WIFI] Connecting to: {{WIFI_SSID}}")
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        attempts = 0
        while not wlan.isconnected() and attempts < 30:
            time.sleep(0.5)
            print(".", end="")
            attempts += 1
    
    if wlan.isconnected():
        print("\\n[WIFI] Connected!")
        print(f"[WIFI] IP Address: {{wlan.ifconfig()[0]}}")
    else:
        print("\\n[WIFI] Connection failed! Running in offline mode.")
    
    return wlan

def load_saved_configuration():
    """Load saved configuration"""
    print("[CONFIG] Loading saved configuration...")
    
    try:
        with open('sensor_config.json', 'r') as f:
            config = ujson.load(f)
            if 'dataEndpoint' in config:
                print(f"[CONFIG] Found saved endpoint: {{config['dataEndpoint']}}")
            if 'pollingInterval' in config:
                print(f"[CONFIG] Found saved interval: {{config['pollingInterval']//1000}}s")
    except:
        print("[CONFIG] No saved configuration found")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

if __name__ == '__main__':
    setup()
    
    while True:
        try:
            loop()
        except KeyboardInterrupt:
            print("\\n[SYSTEM] Shutting down...")
            break
        except Exception as e:
            print(f"[ERROR] {{e}}")
            time.sleep(5)
'''


# Example usage
if __name__ == "__main__":
    # This would normally be called with a database connection
    print("ESP32 Code Generator Service")
    print("=" * 60)
    print("This service generates ESP32 firmware code with offline/online modes")
