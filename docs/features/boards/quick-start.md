# Quick Start: Adding Firebeetle 2 ESP32-C6 Support

## 🎯 What Changed?

The firmware now supports **two board types** with automatic detection:
1. **ESP32-WROOM-32** (Original ESP32)
2. **Firebeetle 2 ESP32-C6** (New RISC-V based board)

## 🚀 Quick Setup

### For ESP32-WROOM-32 (Original)
1. Open `sensor_firmware.ino`
2. Select Board: **ESP32 Dev Module**
3. Upload normally
4. ✅ Done! Board auto-detects as ESP32-WROOM-32

### For Firebeetle 2 ESP32-C6 (New)
1. Open `sensor_firmware.ino` (same file!)
2. Install ESP32 board support 3.0.0+ in Arduino IDE
3. Select Board: **DFRobot Firebeetle 2 ESP32-C6**
4. Tools → USB CDC On Boot → **Enabled**
5. Upload
6. ✅ Done! Board auto-detects as Firebeetle 2 ESP32-C6

## 📌 Pin Differences

The firmware automatically configures the correct pins based on the detected board:

| Function | ESP32-WROOM-32 | Firebeetle 2 C6 |
|----------|----------------|-----------------|
| Temperature Sensor | GPIO4 | GPIO15 |
| Relay Control | GPIO25 | GPIO14 |
| Status LED | GPIO2 | GPIO15 |
| Battery Monitor | GPIO34 | GPIO2 |

**You don't need to change anything in the code!** The firmware handles pin configuration automatically.

## 👀 Viewing Board Types

Navigate to **Sensor Master Control** page:
- Look for the **Board** column in the sensor table
- ESP32-WROOM-32 shows a **blue badge** labeled "ESP32"
- Firebeetle 2 ESP32-C6 shows a **cyan badge** labeled "ESP32-C6"
- Click **View** button for detailed board information

## 🔄 Migration Complete

The database has been updated to track board types:
- ✅ 2 existing sensors updated to ESP32-WROOM-32
- ✅ All future sensors will automatically register with correct board type

## 🆕 What's New in Firmware v2.1.0

- ✨ Automatic board detection at compile time
- 🔧 Board-specific pin configurations
- 📡 Board type reported during registration
- 🎨 UI badges showing board types
- 📚 Complete documentation in `BOARD_SUPPORT.md`

## 💡 Key Features

### Single Firmware for All Boards
- No need to maintain separate firmware files
- Same features work on both boards
- Automatic pin remapping

### Smart Detection
- Detects board at compile time
- Configures pins automatically
- Reports board type to master control

### Clear Visibility
- Dashboard shows which board each sensor uses
- Color-coded badges for easy identification
- Detailed board info in sensor details

## 🐛 Troubleshooting

**Q: My sensor shows "Unknown" board type**  
A: Upload firmware v2.1.0 or later and restart the sensor

**Q: ESP32-C6 won't compile**  
A: You need ESP32 Arduino Core 3.0.0+ for C6 support. Update via Board Manager.

**Q: Wrong pins being used**  
A: Double-check you selected the correct board in Arduino IDE before uploading

**Q: Can I use custom pins?**  
A: Yes! Edit the pin definitions in the firmware header section for your board type

## 📖 Full Documentation

For detailed information, see:
- `BOARD_SUPPORT.md` - Complete board support documentation
- `MULTI_BOARD_SUPPORT_SUMMARY.md` - Implementation details

## 🎉 Next Steps

1. ✅ Database migration complete
2. ✅ Firmware updated with board detection
3. ✅ UI updated to show board types
4. 📤 **Upload new firmware to your ESP32 devices**
5. 🔌 **Acquire Firebeetle 2 ESP32-C6 boards if desired**
6. 🎊 **Enjoy multi-board support!**

---

**Quick Links:**
- [Firebeetle 2 ESP32-C6 Product Page](https://www.dfrobot.com/product-2672.html)
- [ESP32-C6 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf)
- [Arduino ESP32 Board Support](https://github.com/espressif/arduino-esp32)
