# Logic Configuration Examples

This document provides ready-to-use examples for the FireBeetle ESP32-C6 sensor firmware logic system.

## Table of Contents

1. [Battery Monitoring](#battery-monitoring)
2. [Temperature Control](#temperature-control)
3. [Motion Detection](#motion-detection)
4. [Scheduled Actions](#scheduled-actions)
5. [Sensor Data Logging](#sensor-data-logging)
6. [Conditional Alerts](#conditional-alerts)
7. [Advanced Examples](#advanced-examples)

---

## Battery Monitoring

### Basic Battery Status

Read and log battery voltage and percentage:

```json
{
  "alias": "battery_status",
  "interval": 60000,
  "actions": [
    {
      "type": "read_battery",
      "pin": 0,
      "alias": "battery"
    },
    {
      "type": "log",
      "message": "Battery: {battery}V ({battery_pct}%)"
    }
  ]
}
```

### Low Battery Alert

Alert when battery is below 20%:

```json
{
  "alias": "low_battery_alert",
  "interval": 300000,
  "actions": [
    {
      "type": "read_battery",
      "pin": 0,
      "alias": "battery"
    },
    {
      "type": "if",
      "condition": "{battery_pct} < 20",
      "then": [
        {
          "type": "log",
          "message": "⚠️ LOW BATTERY: {battery}V ({battery_pct}%)"
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1,
          "comment": "Turn on LED indicator"
        }
      ],
      "else": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0,
          "comment": "Turn off LED indicator"
        }
      ]
    }
  ]
}
```

### Battery with Custom Calibration

Use custom voltage divider values:

```json
{
  "alias": "custom_battery",
  "actions": [
    {
      "type": "read_battery",
      "pin": 0,
      "alias": "battery",
      "r1": 150000.0,
      "r2": 100000.0,
      "vref": 3.3
    },
    {
      "type": "log",
      "message": "Raw ADC: {battery_raw}, Vout: {battery_vout}V, Battery: {battery}V"
    }
  ]
}
```

---

## Temperature Control

### DHT22 Temperature and Humidity

Read DHT22 sensor and control a fan:

```json
{
  "alias": "climate_control",
  "interval": 10000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "log",
      "message": "Temperature: {temp}°C, Humidity: {temp_humidity}%"
    },
    {
      "type": "if",
      "condition": "{temp} > 28",
      "then": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1,
          "comment": "Turn on fan"
        },
        {
          "type": "log",
          "message": "🌡️ Temperature high, fan ON"
        }
      ],
      "else": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0,
          "comment": "Turn off fan"
        }
      ]
    }
  ]
}
```

### Temperature with Hysteresis

Prevent rapid on/off switching:

```json
{
  "alias": "temp_hysteresis",
  "interval": 5000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "get_variable",
      "name": "fan_state",
      "default": 0,
      "alias": "fan_on"
    },
    {
      "type": "if",
      "condition": "{fan_on} == 0 && {temp} > 30",
      "then": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1
        },
        {
          "type": "set_variable",
          "name": "fan_state",
          "value": 1
        },
        {
          "type": "log",
          "message": "Fan ON at {temp}°C"
        }
      ]
    },
    {
      "type": "if",
      "condition": "{fan_on} == 1 && {temp} < 26",
      "then": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0
        },
        {
          "type": "set_variable",
          "name": "fan_state",
          "value": 0
        },
        {
          "type": "log",
          "message": "Fan OFF at {temp}°C"
        }
      ]
    }
  ]
}
```

---

## Motion Detection

### Basic PIR Motion Sensor

Detect motion and log events:

```json
{
  "alias": "motion_detection",
  "interval": 1000,
  "actions": [
    {
      "type": "read_digital",
      "pin": 4,
      "alias": "motion"
    },
    {
      "type": "if",
      "condition": "{motion} == 1",
      "then": [
        {
          "type": "log",
          "message": "🚨 Motion detected!"
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1,
          "comment": "Turn on light"
        },
        {
          "type": "delay",
          "ms": 5000
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0
        }
      ]
    }
  ]
}
```

### Motion Counter

Count motion events:

```json
{
  "alias": "motion_counter",
  "interval": 500,
  "actions": [
    {
      "type": "read_digital",
      "pin": 4,
      "alias": "motion"
    },
    {
      "type": "get_variable",
      "name": "motion_count",
      "default": 0,
      "alias": "count"
    },
    {
      "type": "get_variable",
      "name": "last_motion",
      "default": 0,
      "alias": "last"
    },
    {
      "type": "if",
      "condition": "{motion} == 1 && {last} == 0",
      "then": [
        {
          "type": "set_variable",
          "name": "motion_count",
          "value": "{count} + 1"
        },
        {
          "type": "set_variable",
          "name": "last_motion",
          "value": 1
        },
        {
          "type": "log",
          "message": "Motion event #{count}"
        }
      ]
    },
    {
      "type": "if",
      "condition": "{motion} == 0",
      "then": [
        {
          "type": "set_variable",
          "name": "last_motion",
          "value": 0
        }
      ]
    }
  ]
}
```

---

## Scheduled Actions

### Time-Based LED Control

Turn LED on during specific hours (requires RTC or NTP):

```json
{
  "alias": "scheduled_led",
  "interval": 60000,
  "actions": [
    {
      "type": "get_variable",
      "name": "current_hour",
      "default": 0,
      "alias": "hour"
    },
    {
      "type": "if",
      "condition": "{hour} >= 18 && {hour} < 23",
      "then": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1,
          "comment": "LED on from 6 PM to 11 PM"
        }
      ],
      "else": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0
        }
      ]
    }
  ]
}
```

### Interval-Based Actions

Perform action every N cycles:

```json
{
  "alias": "periodic_action",
  "interval": 1000,
  "actions": [
    {
      "type": "get_variable",
      "name": "cycle_count",
      "default": 0,
      "alias": "cycles"
    },
    {
      "type": "set_variable",
      "name": "cycle_count",
      "value": "{cycles} + 1"
    },
    {
      "type": "if",
      "condition": "{cycles} % 60 == 0",
      "then": [
        {
          "type": "log",
          "message": "⏰ One minute elapsed (cycle {cycles})"
        },
        {
          "type": "read_battery",
          "pin": 0,
          "alias": "battery"
        },
        {
          "type": "log",
          "message": "Battery check: {battery}V"
        }
      ]
    }
  ]
}
```

---

## Sensor Data Logging

### Multi-Sensor Logger

Log multiple sensors to server:

```json
{
  "alias": "sensor_logger",
  "interval": 30000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "read_analog",
      "pin": 6,
      "alias": "light"
    },
    {
      "type": "read_battery",
      "pin": 0,
      "alias": "battery"
    },
    {
      "type": "http_post",
      "url": "http://server.local/api/sensor-data",
      "data": {
        "temperature": "{temp}",
        "humidity": "{temp_humidity}",
        "light_level": "{light}",
        "battery_voltage": "{battery}",
        "battery_percent": "{battery_pct}"
      }
    }
  ]
}
```

### Conditional Logging

Only log when values change significantly:

```json
{
  "alias": "smart_logger",
  "interval": 5000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "get_variable",
      "name": "last_temp",
      "default": 0,
      "alias": "prev_temp"
    },
    {
      "type": "set_variable",
      "name": "temp_diff",
      "value": "abs({temp} - {prev_temp})"
    },
    {
      "type": "if",
      "condition": "{temp_diff} > 0.5",
      "then": [
        {
          "type": "log",
          "message": "Temperature changed: {prev_temp}°C → {temp}°C"
        },
        {
          "type": "set_variable",
          "name": "last_temp",
          "value": "{temp}"
        },
        {
          "type": "http_post",
          "url": "http://server.local/api/temp",
          "data": {
            "temperature": "{temp}"
          }
        }
      ]
    }
  ]
}
```

---

## Conditional Alerts

### Multiple Threshold Alerts

Different alerts for different ranges:

```json
{
  "alias": "temp_alerts",
  "interval": 10000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "if",
      "condition": "{temp} < 15",
      "then": [
        {
          "type": "log",
          "message": "❄️ COLD: {temp}°C"
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1,
          "comment": "Turn on heater"
        }
      ]
    },
    {
      "type": "if",
      "condition": "{temp} >= 15 && {temp} <= 25",
      "then": [
        {
          "type": "log",
          "message": "✅ COMFORTABLE: {temp}°C"
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0
        },
        {
          "type": "digital_write",
          "pin": 3,
          "value": 0
        }
      ]
    },
    {
      "type": "if",
      "condition": "{temp} > 25",
      "then": [
        {
          "type": "log",
          "message": "🔥 HOT: {temp}°C"
        },
        {
          "type": "digital_write",
          "pin": 3,
          "value": 1,
          "comment": "Turn on cooling"
        }
      ]
    }
  ]
}
```

### Combined Sensor Alert

Alert based on multiple sensor conditions:

```json
{
  "alias": "greenhouse_monitor",
  "interval": 15000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "read_analog",
      "pin": 6,
      "alias": "soil_moisture"
    },
    {
      "type": "if",
      "condition": "{temp} > 30 && {soil_moisture} < 500",
      "then": [
        {
          "type": "log",
          "message": "🌱 ALERT: Hot and dry! Temp: {temp}°C, Moisture: {soil_moisture}"
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1,
          "comment": "Activate irrigation"
        },
        {
          "type": "http_post",
          "url": "http://server.local/api/alerts",
          "data": {
            "alert": "greenhouse_critical",
            "temperature": "{temp}",
            "moisture": "{soil_moisture}"
          }
        }
      ]
    }
  ]
}
```

---

## Advanced Examples

### State Machine

Implement a simple state machine:

```json
{
  "alias": "state_machine",
  "interval": 1000,
  "actions": [
    {
      "type": "get_variable",
      "name": "current_state",
      "default": "idle",
      "alias": "state"
    },
    {
      "type": "read_digital",
      "pin": 4,
      "alias": "trigger"
    },
    {
      "type": "if",
      "condition": "{state} == 'idle' && {trigger} == 1",
      "then": [
        {
          "type": "set_variable",
          "name": "current_state",
          "value": "active"
        },
        {
          "type": "log",
          "message": "State: idle → active"
        },
        {
          "type": "digital_write",
          "pin": 2,
          "value": 1
        }
      ]
    },
    {
      "type": "if",
      "condition": "{state} == 'active'",
      "then": [
        {
          "type": "get_variable",
          "name": "active_timer",
          "default": 0,
          "alias": "timer"
        },
        {
          "type": "set_variable",
          "name": "active_timer",
          "value": "{timer} + 1"
        },
        {
          "type": "if",
          "condition": "{timer} > 10",
          "then": [
            {
              "type": "set_variable",
              "name": "current_state",
              "value": "cooldown"
            },
            {
              "type": "set_variable",
              "name": "active_timer",
              "value": 0
            },
            {
              "type": "log",
              "message": "State: active → cooldown"
            }
          ]
        }
      ]
    },
    {
      "type": "if",
      "condition": "{state} == 'cooldown'",
      "then": [
        {
          "type": "digital_write",
          "pin": 2,
          "value": 0
        },
        {
          "type": "get_variable",
          "name": "cooldown_timer",
          "default": 0,
          "alias": "cd_timer"
        },
        {
          "type": "set_variable",
          "name": "cooldown_timer",
          "value": "{cd_timer} + 1"
        },
        {
          "type": "if",
          "condition": "{cd_timer} > 5",
          "then": [
            {
              "type": "set_variable",
              "name": "current_state",
              "value": "idle"
            },
            {
              "type": "set_variable",
              "name": "cooldown_timer",
              "value": 0
            },
            {
              "type": "log",
              "message": "State: cooldown → idle"
            }
          ]
        }
      ]
    }
  ]
}
```

### PWM Fade Effect

Smoothly fade LED brightness:

```json
{
  "alias": "led_fade",
  "interval": 50,
  "actions": [
    {
      "type": "get_variable",
      "name": "brightness",
      "default": 0,
      "alias": "level"
    },
    {
      "type": "get_variable",
      "name": "fade_direction",
      "default": 1,
      "alias": "dir"
    },
    {
      "type": "analog_write",
      "pin": 2,
      "value": "{level}"
    },
    {
      "type": "set_variable",
      "name": "brightness",
      "value": "{level} + ({dir} * 5)"
    },
    {
      "type": "if",
      "condition": "{level} >= 255",
      "then": [
        {
          "type": "set_variable",
          "name": "fade_direction",
          "value": -1
        }
      ]
    },
    {
      "type": "if",
      "condition": "{level} <= 0",
      "then": [
        {
          "type": "set_variable",
          "name": "fade_direction",
          "value": 1
        }
      ]
    }
  ]
}
```

### Servo Sweep

Sweep servo back and forth:

```json
{
  "alias": "servo_sweep",
  "interval": 20,
  "actions": [
    {
      "type": "get_variable",
      "name": "servo_pos",
      "default": 0,
      "alias": "pos"
    },
    {
      "type": "get_variable",
      "name": "servo_dir",
      "default": 1,
      "alias": "dir"
    },
    {
      "type": "servo_write",
      "pin": 3,
      "angle": "{pos}"
    },
    {
      "type": "set_variable",
      "name": "servo_pos",
      "value": "{pos} + {dir}"
    },
    {
      "type": "if",
      "condition": "{pos} >= 180",
      "then": [
        {
          "type": "set_variable",
          "name": "servo_dir",
          "value": -1
        }
      ]
    },
    {
      "type": "if",
      "condition": "{pos} <= 0",
      "then": [
        {
          "type": "set_variable",
          "name": "servo_dir",
          "value": 1
        }
      ]
    }
  ]
}
```

---

## Best Practices

### 1. Use Meaningful Aliases

```json
// Good
{"type": "read_dht22", "pin": 5, "alias": "living_room_temp"}

// Avoid
{"type": "read_dht22", "pin": 5, "alias": "t1"}
```

### 2. Add Comments

```json
{
  "type": "digital_write",
  "pin": 2,
  "value": 1,
  "comment": "Turn on relay for water pump"
}
```

### 3. Set Appropriate Intervals

```json
// Fast response (motion detection)
{"alias": "motion", "interval": 100}

// Normal monitoring (temperature)
{"alias": "temp", "interval": 5000}

// Slow logging (battery)
{"alias": "battery", "interval": 60000}
```

### 4. Use Hysteresis for Thresholds

Prevent rapid switching by using different on/off thresholds:

```json
// Turn on at 30°C, turn off at 26°C
```

### 5. Validate Sensor Readings

```json
{
  "type": "if",
  "condition": "{temp} > -50 && {temp} < 100",
  "then": [
    {"type": "log", "message": "Valid temp: {temp}°C"}
  ],
  "else": [
    {"type": "log", "message": "⚠️ Invalid temp reading: {temp}"}
  ]
}
```

---

## Debugging Tips

### Enable Verbose Logging

```json
{
  "type": "log",
  "message": "DEBUG: temp={temp}, motion={motion}, battery={battery}"
}
```

### Check Raw Values

```json
{
  "type": "read_analog",
  "pin": 6,
  "alias": "sensor"
},
{
  "type": "log",
  "message": "Raw ADC value: {sensor}"
}
```

### Use Serial Monitor

```bash
pio device monitor --baud 115200
```

---

**Last Updated**: December 29, 2025
