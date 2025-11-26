# Sensor Master Control System

## Overview

The Sensor Master Control system enables centralized management and configuration of IoT sensors (like ESP32 devices). Sensors can "phone home" to your application to receive their configuration instructions dynamically, rather than relying solely on hardcoded firmware settings.

**Simplified Architecture**: Sensors connect directly to your application instance - no complex master instance management needed.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Sensor Ecosystem                          │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  ESP32 #1   │    │  ESP32 #2   │    │  ESP32 #3   │      │
│  │  (Sensor)   │    │  (Sensor)   │    │  (Sensor)   │      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘      │
│         │                   │                   │              │
│         │ 1. Register       │ 1. Register       │ 1. Register │
│         │ 2. Get Config     │ 2. Get Config     │ 2. Get Config│
│         │ 3. Heartbeat      │ 3. Heartbeat      │ 3. Heartbeat│
│         │ 4. Send Data      │ 4. Send Data      │ 4. Send Data│
│         └───────────────────┴───────────────────┘              │
│                             │                                   │
│                             ▼                                   │
│         ┌─────────────────────────────────────┐                │
│         │   Your Application (Port 5000)      │                │
│         │   ┌─────────────────────────────┐   │                │
│         │   │  Sensor Master Control      │   │                │
│         │   │  - Manages sensor configs   │   │                │
│         │   │  - Tracks sensor status     │   │                │
│         │   │  - Receives sensor data     │   │                │
│         │   │  - Queues commands          │   │                │
│         │   └─────────────────────────────┘   │                │
│         │                                       │                │
│         │   Provides:                           │                │
│         │   - Configuration templates          │                │
│         │   - Polling intervals                │                │
│         │   - Sensor mappings                  │                │
│         │   - Dynamic script updates           │                │
│         └─────────────────────────────────────┘                │
│                                                                 │
└──────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Sensor Registration
When a sensor boots up (or periodically), it:
1. Sends a registration request to your application
2. Receives confirmation and configuration availability
3. Retrieves its configuration settings

### Configuration Priority
Configuration is applied in this order:
1. **Sensor-specific config** - Configuration for a specific sensor ID
2. **Type-specific config** - Configuration for all sensors of a type (e.g., all `esp32_fermentation` sensors)
3. **Fallback/local config** - Hardcoded or local configuration

### Configuration Hash
Each configuration has a hash that allows sensors to detect when their configuration has changed, triggering updates without constant polling.

## Database Schema

### SensorRegistration
Tracks all registered sensors:
- `sensor_id` - Unique identifier for the sensor
- `sensor_type` - Type of sensor (e.g., `esp32_fermentation`)
- `last_check_in` - Last time sensor contacted the system
- `status` - Current status (`online`, `offline`, `pending`)
- `config_hash` - Hash of current configuration
- `ip_address`, `mac_address` - Network information
- `capabilities` - JSON array of sensor capabilities

### SensorMasterConfig
Stores configuration templates:
- `sensor_id` - Apply to specific sensor (NULL for type-based)
- `sensor_type` - Apply to all sensors of this type
- `config_name` - Friendly name for the configuration
- `config_data` - JSON configuration
- `priority` - Configuration priority (lower = higher priority)
- `is_active` - Whether this configuration is active

### SensorCommandQueue
Queue commands for sensors:
- `sensor_id` - Target sensor
- `command_type` - Type of command (`update_config`, `restart`, etc.)
- `command_data` - Command payload
- `status` - Command status (`pending`, `delivered`, `completed`)
- `priority` - Command priority
- `expires_at` - When the command expires

## Setup Guide

### 1. Enable Sensor Master Control

1. Navigate to **Settings** in your app
2. Enable **Sensor Master Control** toggle
3. Navigate to **Sensor Master Control** page
   - **Description**: Purpose of this master
   - **API Endpoint**: External URL (e.g., `http://192.168.1.100:5000`)
   - **Priority**: 1 for primary master
   - **Enable**: Check to activate

4. Click **Save**

### 2. Create Configuration Template

1. In the **Configuration Templates** section, click **New Template**
2. Configure:
   - **Master Instance**: Select your master
   - **Template Name**: e.g., "Default ESP32 Fermentation Config"
   - **Apply To**: Choose "All sensors of type" or "Specific sensor"
   - **Configuration (JSON)**: Define the config (see example below)

3. Example configuration:
```json
{
  "polling_interval": 60,
  "data_endpoint": "http://192.168.1.101:5001/api/devices/data",
  "retry_attempts": 3,
  "retry_delay": 5,
  "sensor_mappings": [
    {
      "sensor_name": "sensor.temperature",
      "entry_field": "Temperature",
      "unit": "°C",
      "data_type": "float"
    },
    {
      "sensor_name": "sensor.target",
      "entry_field": "Target Temperature",
      "unit": "°C",
      "data_type": "float"
    },
    {
      "sensor_name": "relay.state",
      "entry_field": "Relay State",
      "unit": "",
      "data_type": "text"
    }
  ],
  "linked_entries": [1, 2, 3],
  "features": {
    "auto_recording": true,
    "notifications": true
  }
}
```

4. Click **Save**

### 3. Flash ESP32 Sensor

Use the provided templates in `scripts/esp32_master_control_integration.py`:

**For Arduino/C++:**
```cpp
const char* MASTER_CONTROL_URL = "http://192.168.1.100:5000";
const char* SENSOR_ID = "esp32_fermentation_001";
const char* SENSOR_TYPE = "esp32_fermentation";
```

**For MicroPython:**
```python
MASTER_CONTROL_URL = "http://192.168.1.100:5000"
SENSOR_ID = "esp32_fermentation_001"
SENSOR_TYPE = "esp32_fermentation"
```

### 4. Monitor Sensors

1. Return to **Sensor Master Control** page
2. View **Registered Sensors** section
3. Monitor:
   - Online/offline status
   - Last check-in time
   - Configuration assignment
   - Capabilities

## API Endpoints

### Sensor-Side Endpoints (called by ESP32)

#### Register Sensor
```
POST /api/sensor-master/register
```

**Request:**
```json
{
  "sensor_id": "esp32_fermentation_001",
  "sensor_name": "Fermentation Chamber 1",
  "sensor_type": "esp32_fermentation",
  "hardware_info": "ESP32-WROOM-32",
  "firmware_version": "1.0.0",
  "ip_address": "192.168.1.150",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "capabilities": ["temperature", "relay_control"]
}
```

**Response:**
```json
{
  "status": "registered",
  "assigned_master": "Production Master",
  "master_id": 1,
  "has_config": true,
  "check_in_interval": 60,
  "config_endpoint": "/api/sensor-master/config/esp32_fermentation_001"
}
```

#### Get Configuration
```
GET /api/sensor-master/config/{sensor_id}
```

**Response:**
```json
{
  "config_available": true,
  "config_changed": true,
  "config_hash": "abc123...",
  "config_name": "Default ESP32 Config",
  "config_version": 1,
  "config": {
    "polling_interval": 60,
    "data_endpoint": "http://192.168.1.101:5001/api/devices/data",
    "sensor_mappings": [...]
  },
  "commands": [],
  "check_in_interval": 60
}
```

#### Send Heartbeat
```
POST /api/sensor-master/heartbeat
```

**Request:**
```json
{
  "sensor_id": "esp32_fermentation_001",
  "status": "online",
  "metrics": {
    "uptime": 3600,
    "free_memory": 80000,
    "wifi_rssi": -45
  }
}
```

### Management Endpoints (web interface)

- `GET /api/sensor-master/instances` - List master instances
- `POST /api/sensor-master/instances` - Create master instance
- `PATCH /api/sensor-master/instances/{id}` - Update master instance
- `DELETE /api/sensor-master/instances/{id}` - Delete master instance
- `GET /api/sensor-master/sensors` - List registered sensors
- `PATCH /api/sensor-master/sensors/{sensor_id}` - Update sensor
- `DELETE /api/sensor-master/sensors/{sensor_id}` - Unregister sensor
- `GET /api/sensor-master/configs` - List configurations
- `POST /api/sensor-master/configs` - Create configuration
- `PATCH /api/sensor-master/configs/{id}` - Update configuration
- `DELETE /api/sensor-master/configs/{id}` - Delete configuration
- `POST /api/sensor-master/command` - Queue command for sensor
- `GET /api/sensor-master/commands` - View command queue

## Use Cases

### 1. Central Configuration Management
Instead of flashing new firmware every time you change a sensor's data endpoint or polling interval, update the configuration in the master control web interface. The sensor will receive the new config on its next check-in.

### 2. Multi-Instance Data Collection
- **Instance A**: Master control (http://192.168.1.100:5000)
- **Instance B**: Production data collector (http://192.168.1.101:5001)
- **Instance C**: Development data collector (http://192.168.1.102:5002)

Configure sensors to send data to Instance B or C without reflashing.

### 3. Sensor Migration
Move a sensor from one data collector to another:
1. Edit the sensor's configuration
2. Update `data_endpoint` to new instance
3. Sensor receives update on next check-in
4. Data flows to new destination

### 4. Remote Commands
Queue commands for sensors:
```python
# Queue a configuration update
POST /api/sensor-master/command
{
  "sensor_id": "esp32_fermentation_001",
  "command_type": "update_config"
}

# Queue a restart
POST /api/sensor-master/command
{
  "sensor_id": "esp32_fermentation_001",
  "command_type": "restart"
}

# Queue a parameter change
POST /api/sensor-master/command
{
  "sensor_id": "esp32_fermentation_001",
  "command_type": "set_target_temp",
  "command_data": {
    "target": 18.5
  }
}
```

### 5. Fallback Mode
If master control is unavailable:
- Sensor uses hardcoded fallback configuration
- Data still collected locally or sent to fallback endpoint
- Sensor automatically reconnects when master comes back online

## Best Practices

### 1. Use Unique Sensor IDs
Generate unique identifiers for each sensor:
```
esp32_fermentation_001
esp32_fermentation_002
esp32_ph_001
esp32_temp_basement_001
```

### 2. Type-Based Configuration
Create type-based configs for common settings, then override with sensor-specific configs for exceptions.

### 3. Monitoring
Set up alerts for:
- Sensors that haven't checked in recently
- Configuration delivery failures
- Command execution failures

### 4. Security
- Use API keys for production deployments
- Implement SSL/TLS for encrypted communication
- Restrict network access to trusted sensors

### 5. Testing
- Test configuration changes on a single sensor first
- Use development master control instance for testing
- Keep fallback configurations working

## Troubleshooting

### Sensor Not Registering
1. Check network connectivity
2. Verify MASTER_CONTROL_URL is correct
3. Check master control instance is enabled
4. Review sensor logs for error messages

### Configuration Not Updating
1. Check config_hash to see if it changed
2. Verify sensor is checking in regularly
3. Check configuration is active and assigned correctly
4. Review command queue for pending updates

### Data Not Reaching Destination
1. Verify data_endpoint in configuration
2. Check target instance is running
3. Test endpoint manually with curl/Postman
4. Review sensor logs for HTTP errors

### Master Control Offline
- Sensors automatically fall back to local configuration
- Data continues to be collected
- Sensors will reconnect when master comes back

## Advanced Features

### Multiple Master Instances
Deploy multiple master control instances with different priorities:
- Priority 1: Production master
- Priority 2: Backup master
- Priority 3: Development master

Sensors automatically fail over to next priority if primary is unavailable.

### Configuration Versioning
Track configuration changes with version numbers. Sensors can request specific versions or always get latest.

### Sensor Groups
Create sensor groups with shared configurations:
```json
{
  "group_name": "fermentation_floor_1",
  "sensors": ["esp32_001", "esp32_002", "esp32_003"],
  "config": {...}
}
```

### Analytics Dashboard
Monitor sensor health, check-in patterns, configuration compliance, and command execution rates.

## Integration with Existing System

The Sensor Master Control integrates seamlessly with:
- **RegisteredDevices**: Sensors can be both registered devices and master-controlled
- **DeviceEntryLinks**: Configuration can specify entry links
- **DeviceSensorMapping**: Master control can override sensor mappings
- **Device Scheduler**: Polling can be managed by master or locally

## Migration Guide

### Existing Sensors
To migrate existing sensors to master control:

1. Register sensors in Sensor Master Control
2. Create configuration template matching current behavior
3. Update ESP32 firmware to include master control code
4. Flash updated firmware
5. Verify sensor registers and receives config
6. Monitor for 24 hours
7. Gradually move configuration management to master

### Rollback Plan
If issues arise:
1. Disable master control instance
2. Sensors fall back to local configuration
3. System operates as before
4. Debug and re-enable when ready

## Support and Resources

- **ESP32 Examples**: `scripts/esp32_master_control_integration.py`
- **API Documentation**: This file
- **Management UI**: `/sensor-master-control`
- **API Base URL**: `/api/sensor-master/`

## Future Enhancements

Potential future features:
- OTA firmware updates via master control
- Sensor discovery and auto-configuration
- Machine learning for optimal polling intervals
- Encrypted configuration storage
- Role-based access control for multi-tenant setups
- Mobile app for sensor management
- Real-time sensor dashboard with WebSocket updates
- Sensor performance analytics and optimization suggestions

---

**Version**: 1.0.0  
**Created**: November 21, 2025  
**Status**: Production Ready
