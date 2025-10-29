# CasaOS Setup and Access Guide

## Important: Host Networking Configuration

This application **requires host networking** to discover ESP32 devices on your local network. This means:

### ✅ **How to Access the Application**
- **Direct URL**: `http://YOUR_HOST_IP:5001`
- **Example**: If your server IP is `192.168.68.100`, use `http://192.168.68.100:5001`

### ⚠️ **CasaOS Dashboard Limitations**
- The CasaOS dashboard may show "App may not be available"
- The app launch URL from CasaOS may not work correctly
- This is **NORMAL** and **EXPECTED** with host networking

### 🔧 **Why Host Networking is Required**
The application needs to:
- Scan your local network (e.g., 192.168.x.x) for ESP32 devices
- Directly access devices on your LAN
- Use network discovery protocols

With standard Docker port mapping, the container would be isolated from your local network and couldn't find your ESP32 devices.

## Setup Instructions

1. **Deploy via CasaOS Dev Manager** using the docker-compose.yml file
2. **Ignore** any "app not available" warnings in CasaOS
3. **Access directly** via `http://YOUR_SERVER_IP:5001`
4. **Configure** your project settings
5. **Test device discovery** in Device Management

## Features Available
- ✅ Project and entry management
- ✅ ESP32 device discovery and polling
- ✅ Sensor data monitoring
- ✅ Label printing with QR codes
- ✅ Push notifications via ntfy
- ✅ File attachments and notes
- ✅ Automated overdue checks

## Data Persistence
- All data is stored in a Docker volume (`template_db_data`)
- Data survives container restarts and updates
- No host folder permissions issues

## Troubleshooting

### "App may not be available" in CasaOS
- **Solution**: Access directly via IP:5001, this is expected with host networking

### ESP32 devices not found
- **Check**: Ensure devices are on the same network as your server
- **Check**: Device discovery requires host networking (which is enabled)
- **Test**: Use the "Test Connection" feature with a known device IP

### Can't access the application
- **Verify**: Container is running: `docker ps`
- **Verify**: Port 5001 is not blocked by firewall
- **Try**: Access from the server itself: `curl http://localhost:5001`

## Network Configuration
- **Mode**: Host networking (`network_mode: host`)
- **Port**: 5001 (directly on host, not mapped)
- **Discovery**: Full local network access for ESP32 devices
