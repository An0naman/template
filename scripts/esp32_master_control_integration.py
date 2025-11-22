"""
ESP32 Sensor Master Control Integration
========================================

This file contains example code and helper functions for ESP32 sensors to integrate
with the Sensor Master Control system.

The basic workflow is:
1. On boot, sensor attempts to register with master control
2. If successful, sensor retrieves its configuration
3. Sensor periodically checks in and executes any pending commands
4. If master control unavailable, sensor uses local/fallback configuration
"""

# ==============================================================================
# EXAMPLE: Arduino/C++ Code for ESP32
# ==============================================================================

ARDUINO_EXAMPLE = '''
/*
 * ESP32 Sensor with Master Control Integration
 * 
 * This example shows how to integrate an ESP32 sensor with the 
 * Sensor Master Control system.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configuration
const char* WIFI_SSID = "YourWiFiSSID";
const char* WIFI_PASSWORD = "YourWiFiPassword";
const char* MASTER_CONTROL_URL = "http://192.168.1.100:5000";  // Your master control instance
const char* SENSOR_ID = "esp32_fermentation_001";  // Unique sensor ID
const char* SENSOR_TYPE = "esp32_fermentation";

// State
bool masterControlActive = false;
String dataEndpoint = "";
int pollingInterval = 60;  // seconds
unsigned long lastCheckIn = 0;
unsigned long lastDataSend = 0;

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\\nWiFi connected");
  
  // Initialize sensor hardware
  initializeSensors();
  
  // Attempt to register with master control
  registerWithMaster();
  
  // Get configuration from master
  if (masterControlActive) {
    getConfigFromMaster();
  } else {
    // Use local configuration
    useFallbackConfig();
  }
}

void loop() {
  unsigned long currentTime = millis();
  
  // Read sensors
  float temperature = readTemperature();
  float targetTemp = getTargetTemperature();
  bool relayState = getRelayState();
  
  // Send data at configured interval
  if (currentTime - lastDataSend >= pollingInterval * 1000) {
    if (masterControlActive && dataEndpoint.length() > 0) {
      sendDataToMaster(temperature, targetTemp, relayState);
    } else {
      // Send to local endpoint or store locally
      sendDataLocal(temperature, targetTemp, relayState);
    }
    lastDataSend = currentTime;
  }
  
  // Check in with master control every 5 minutes
  if (masterControlActive && currentTime - lastCheckIn >= 300000) {
    sendHeartbeat();
    
    // Re-check configuration in case it changed
    getConfigFromMaster();
    
    lastCheckIn = currentTime;
  }
  
  delay(1000);
}

bool registerWithMaster() {
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/register";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Build registration payload
  StaticJsonDocument<512> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["sensor_name"] = "Fermentation Chamber 1";
  doc["sensor_type"] = SENSOR_TYPE;
  doc["hardware_info"] = "ESP32-WROOM-32";
  doc["firmware_version"] = "1.0.0";
  doc["ip_address"] = WiFi.localIP().toString();
  doc["mac_address"] = WiFi.macAddress();
  
  JsonArray capabilities = doc.createNestedArray("capabilities");
  capabilities.add("temperature");
  capabilities.add("relay_control");
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<512> responseDoc;
    deserializeJson(responseDoc, response);
    
    if (responseDoc["status"] == "registered") {
      masterControlActive = true;
      Serial.println("Registered with master control: " + String(responseDoc["assigned_master"].as<String>()));
      http.end();
      return true;
    }
  }
  
  Serial.println("Master control not available, using local mode");
  masterControlActive = false;
  http.end();
  return false;
}

bool getConfigFromMaster() {
  if (!masterControlActive) return false;
  
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/config/" + SENSOR_ID;
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<1024> doc;
    deserializeJson(doc, response);
    
    if (doc["config_available"]) {
      // Update configuration from master
      pollingInterval = doc["config"]["polling_interval"] | 60;
      dataEndpoint = doc["config"]["data_endpoint"].as<String>();
      
      // Check if config changed
      if (doc["config_changed"]) {
        Serial.println("Configuration updated from master");
        // Apply new sensor mappings, etc.
      }
      
      // Process any pending commands
      if (doc["commands"].size() > 0) {
        processCommands(doc["commands"]);
      }
      
      http.end();
      return true;
    }
  }
  
  http.end();
  return false;
}

void sendHeartbeat() {
  HTTPClient http;
  String url = String(MASTER_CONTROL_URL) + "/api/sensor-master/heartbeat";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
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
  
  http.POST(payload);
  http.end();
}

void sendDataToMaster(float temperature, float targetTemp, bool relayState) {
  HTTPClient http;
  http.begin(dataEndpoint);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<512> doc;
  doc["device_id"] = SENSOR_ID;
  doc["timestamp"] = millis();
  
  JsonObject sensor = doc.createNestedObject("sensor");
  sensor["temperature"] = temperature;
  sensor["target"] = targetTemp;
  sensor["valid"] = true;
  
  JsonObject relay = doc.createNestedObject("relay");
  relay["state"] = relayState ? "on" : "off";
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    Serial.println("Data sent to master successfully");
  } else {
    Serial.println("Failed to send data: " + String(httpCode));
  }
  
  http.end();
}

void processCommands(JsonArray commands) {
  for (JsonObject cmd : commands) {
    String commandType = cmd["command_type"];
    int commandId = cmd["id"];
    
    Serial.println("Processing command: " + commandType);
    
    if (commandType == "update_config") {
      // Re-fetch configuration
      getConfigFromMaster();
    } 
    else if (commandType == "restart") {
      // Restart the ESP32
      ESP.restart();
    }
    else if (commandType == "set_target_temp") {
      float newTarget = cmd["command_data"]["target"];
      setTargetTemperature(newTarget);
    }
    
    // Report command execution result back to master
    // (This would be sent in the next heartbeat)
  }
}

void useFallbackConfig() {
  Serial.println("Using fallback configuration");
  pollingInterval = 60;
  dataEndpoint = "http://192.168.1.100:5000/api/devices/data";  // Your fallback endpoint
}

// Sensor functions (implement based on your hardware)
void initializeSensors() {
  // Initialize temperature sensor, relay, etc.
}

float readTemperature() {
  // Read from your temperature sensor
  return 20.5;  // Example
}

float getTargetTemperature() {
  // Get target temperature from your control logic
  return 18.0;  // Example
}

bool getRelayState() {
  // Get relay state
  return false;  // Example
}

void setTargetTemperature(float temp) {
  // Set target temperature
}

void sendDataLocal(float temperature, float targetTemp, bool relayState) {
  // Store data locally or send to fallback endpoint
  Serial.println("Using local data storage/endpoint");
}
'''

# ==============================================================================
# EXAMPLE: MicroPython Code for ESP32
# ==============================================================================

MICROPYTHON_EXAMPLE = '''
"""
ESP32 Sensor with Master Control Integration (MicroPython)
"""

import network
import urequests
import ujson
import time
import machine

# Configuration
WIFI_SSID = "YourWiFiSSID"
WIFI_PASSWORD = "YourWiFiPassword"
MASTER_CONTROL_URL = "http://192.168.1.100:5000"
SENSOR_ID = "esp32_fermentation_001"
SENSOR_TYPE = "esp32_fermentation"

# State
master_control_active = False
data_endpoint = ""
polling_interval = 60
last_check_in = 0
last_data_send = 0

def connect_wifi():
    """Connect to WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        while not wlan.isconnected():
            time.sleep(0.5)
    
    print('WiFi connected:', wlan.ifconfig())
    return wlan

def register_with_master():
    """Register sensor with master control"""
    global master_control_active
    
    url = f"{MASTER_CONTROL_URL}/api/sensor-master/register"
    
    payload = {
        "sensor_id": SENSOR_ID,
        "sensor_name": "Fermentation Chamber 1",
        "sensor_type": SENSOR_TYPE,
        "hardware_info": "ESP32",
        "firmware_version": "1.0.0",
        "capabilities": ["temperature", "relay_control"]
    }
    
    try:
        response = urequests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'registered':
                master_control_active = True
                print(f"Registered with master: {data.get('assigned_master')}")
                response.close()
                return True
        
        response.close()
    except Exception as e:
        print(f"Failed to register with master: {e}")
    
    master_control_active = False
    print("Using local mode")
    return False

def get_config_from_master():
    """Get configuration from master control"""
    global polling_interval, data_endpoint
    
    if not master_control_active:
        return False
    
    url = f"{MASTER_CONTROL_URL}/api/sensor-master/config/{SENSOR_ID}"
    
    try:
        response = urequests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('config_available'):
                config = data.get('config', {})
                polling_interval = config.get('polling_interval', 60)
                data_endpoint = config.get('data_endpoint', '')
                
                if data.get('config_changed'):
                    print("Configuration updated from master")
                
                # Process commands if any
                commands = data.get('commands', [])
                if commands:
                    process_commands(commands)
                
                response.close()
                return True
        
        response.close()
    except Exception as e:
        print(f"Failed to get config: {e}")
    
    return False

def send_heartbeat():
    """Send heartbeat to master control"""
    if not master_control_active:
        return
    
    url = f"{MASTER_CONTROL_URL}/api/sensor-master/heartbeat"
    
    payload = {
        "sensor_id": SENSOR_ID,
        "status": "online",
        "metrics": {
            "uptime": time.ticks_ms() // 1000,
            "free_memory": machine.mem_free()
        }
    }
    
    try:
        response = urequests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response.close()
    except Exception as e:
        print(f"Heartbeat failed: {e}")

def send_data_to_master(temperature, target_temp, relay_state):
    """Send sensor data to master control"""
    if not data_endpoint:
        return
    
    payload = {
        "device_id": SENSOR_ID,
        "timestamp": time.ticks_ms(),
        "sensor": {
            "temperature": temperature,
            "target": target_temp,
            "valid": True
        },
        "relay": {
            "state": "on" if relay_state else "off"
        }
    }
    
    try:
        response = urequests.post(data_endpoint, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            print("Data sent successfully")
        else:
            print(f"Failed to send data: {response.status_code}")
        
        response.close()
    except Exception as e:
        print(f"Failed to send data: {e}")

def process_commands(commands):
    """Process commands from master control"""
    for cmd in commands:
        command_type = cmd.get('command_type')
        print(f"Processing command: {command_type}")
        
        if command_type == 'update_config':
            get_config_from_master()
        elif command_type == 'restart':
            machine.reset()
        elif command_type == 'set_target_temp':
            new_target = cmd.get('command_data', {}).get('target')
            # Set target temperature
            print(f"Setting target temperature to {new_target}")

def main():
    """Main loop"""
    global last_check_in, last_data_send
    
    # Connect to WiFi
    wlan = connect_wifi()
    
    # Initialize sensors
    # initialize_sensors()
    
    # Register with master control
    register_with_master()
    
    # Get initial configuration
    if master_control_active:
        get_config_from_master()
    
    # Main loop
    while True:
        current_time = time.ticks_ms()
        
        # Read sensors
        temperature = read_temperature()
        target_temp = get_target_temperature()
        relay_state = get_relay_state()
        
        # Send data at configured interval
        if time.ticks_diff(current_time, last_data_send) >= polling_interval * 1000:
            if master_control_active and data_endpoint:
                send_data_to_master(temperature, target_temp, relay_state)
            last_data_send = current_time
        
        # Check in every 5 minutes
        if master_control_active and time.ticks_diff(current_time, last_check_in) >= 300000:
            send_heartbeat()
            get_config_from_master()
            last_check_in = current_time
        
        time.sleep(1)

# Sensor functions (implement based on your hardware)
def read_temperature():
    """Read temperature from sensor"""
    return 20.5  # Example

def get_target_temperature():
    """Get target temperature"""
    return 18.0  # Example

def get_relay_state():
    """Get relay state"""
    return False  # Example

if __name__ == '__main__':
    main()
'''

# ==============================================================================
# Helper Functions for Generating Configuration
# ==============================================================================

def generate_esp32_config(sensor_id, master_url, sensor_type="esp32_fermentation"):
    """
    Generate a configuration for ESP32 firmware
    
    Args:
        sensor_id: Unique sensor identifier
        master_url: URL of the master control instance
        sensor_type: Type of sensor
        
    Returns:
        Dictionary with configuration
    """
    return {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "master_control_url": master_url,
        "fallback_endpoint": f"{master_url}/api/devices/data",
        "check_in_interval": 300,  # 5 minutes
        "polling_interval": 60,  # 1 minute
        "retry_attempts": 3,
        "retry_delay": 5
    }


def generate_arduino_sketch(sensor_id, master_url, wifi_ssid, wifi_password):
    """
    Generate a complete Arduino sketch with configuration
    
    Args:
        sensor_id: Unique sensor identifier
        master_url: URL of the master control instance
        wifi_ssid: WiFi SSID
        wifi_password: WiFi password
        
    Returns:
        String with Arduino sketch
    """
    config = generate_esp32_config(sensor_id, master_url)
    
    sketch = ARDUINO_EXAMPLE.replace('WIFI_SSID = "YourWiFiSSID"', f'WIFI_SSID = "{wifi_ssid}"')
    sketch = sketch.replace('WIFI_PASSWORD = "YourWiFiPassword"', f'WIFI_PASSWORD = "{wifi_password}"')
    sketch = sketch.replace('MASTER_CONTROL_URL = "http://192.168.1.100:5000"', f'MASTER_CONTROL_URL = "{master_url}"')
    sketch = sketch.replace('SENSOR_ID = "esp32_fermentation_001"', f'SENSOR_ID = "{sensor_id}"')
    
    return sketch


if __name__ == "__main__":
    # Example usage
    print("ESP32 Sensor Master Control Integration Examples")
    print("=" * 60)
    print("\n1. Arduino/C++ Example:")
    print(ARDUINO_EXAMPLE[:500] + "...")
    print("\n2. MicroPython Example:")
    print(MICROPYTHON_EXAMPLE[:500] + "...")
    
    # Generate custom config
    config = generate_esp32_config("my_sensor_001", "http://192.168.1.100:5000")
    print("\n3. Generated Configuration:")
    import json
    print(json.dumps(config, indent=2))
