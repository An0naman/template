# Quick Start Guide - FireBeetle ESP32-C6

## 🚀 5-Minute Setup

### 1. Flash Firmware
```bash
cd firmware/firebeetle_esp32c6
pio run -e firebeetle2_esp32c6 -t upload
```

### 2. Connect to Device
- SSID: `ESP32-Setup-XXXXXX`
- Password: `12345678`
- Open: http://192.168.4.1

### 3. Configure WiFi
Enter your network credentials and save.

### 4. Access on Your Network
Find device IP in router, then access web interface.

---

## 📁 Files in This Directory

- **sensor_firmware.ino** - Main firmware (2100+ lines)
- **esp32_web_interface.h** - Web UI (HTML/JS)
- **platformio.ini** - Build configuration
- **README.md** - Complete documentation
- **LOGIC_EXAMPLES.md** - Ready-to-use configurations
- **QUICKSTART.md** - This file

---

## 🔋 Battery Monitoring (Quick Test)

```json
{
  "alias": "battery_test",
  "interval": 5000,
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

Paste this into Logic Editor → Save → Check Serial Monitor

---

## 🌡️ Temperature Sensor (DHT22)

```json
{
  "alias": "temp_monitor",
  "interval": 10000,
  "actions": [
    {
      "type": "read_dht22",
      "pin": 5,
      "alias": "temp"
    },
    {
      "type": "log",
      "message": "Temp: {temp}°C, Humidity: {temp_humidity}%"
    }
  ]
}
```

Connect DHT22:
- VCC → 3.3V
- GND → GND
- DATA → GPIO 5

---

## 🔧 Common Commands

### Build
```bash
pio run -e firebeetle2_esp32c6
```

### Upload
```bash
pio run -e firebeetle2_esp32c6 -t upload
```

### Monitor
```bash
pio device monitor --baud 115200
```

### Clean
```bash
pio run -e firebeetle2_esp32c6 -t clean
```

---

## 🐛 Troubleshooting

### Can't Connect to ESP32 AP
- Hold BOOT button and reset
- Wait 30 seconds for AP to start
- Check if LED is blinking

### Upload Fails
```bash
# Hold BOOT button during upload
# Or use:
pio run -e firebeetle2_esp32c6 -t upload --upload-port /dev/ttyUSB0
```

### Wrong Battery Reading
- Verify GPIO 0 (not another pin)
- Check if battery is connected
- Serial monitor will show raw ADC value

### Serial Monitor Shows Gibberish
- Set baud rate to 115200
- Try: `pio device monitor --baud 115200`

---

## 📚 More Information

- **Complete Documentation**: [README.md](README.md)
- **Logic Examples**: [LOGIC_EXAMPLES.md](LOGIC_EXAMPLES.md)
- **Hardware Wiki**: https://wiki.dfrobot.com/SKU_DFR1075_FireBeetle_2_Board_ESP32_C6

---

## ⚡ Quick Pin Reference

### GPIO 0
Battery voltage detection (built-in divider)

### GPIO 2
General purpose, has built-in LED

### GPIO 5
Good for DHT sensors

### GPIO 6
Analog input

### GPIO 8-9
I2C (SDA/SCL)

---

**Ready to start?** See [LOGIC_EXAMPLES.md](LOGIC_EXAMPLES.md) for copy-paste configurations!
