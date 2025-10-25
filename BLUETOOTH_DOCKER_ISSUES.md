# Bluetooth/Niimbot Printing - Docker Issues and Solutions

## The Problem

Bluetooth Low Energy (BLE) connections from inside Docker containers are notoriously problematic due to:
- Limited D-Bus access
- Bluetooth stack isolation
- Permission and capability restrictions
- Kernel module requirements

Even with `--privileged` mode and all the correct volume mounts, BLE connections often fail.

## Solution Options

### Option 1: Run Application Directly (RECOMMENDED)

The easiest and most reliable way to use Niimbot printers is to run the Flask application **directly on your host** instead of in Docker:

```bash
# Stop the Docker container
docker compose down

# Run the application with Bluetooth support
./run_with_bluetooth.sh
```

This script will:
1. Create a Python virtual environment
2. Install all dependencies (including bleak for Bluetooth)
3. Run the Flask app directly on your host
4. Give you full Bluetooth access

Access the application at: `http://localhost:5001`

### Option 2: Use Docker for Everything Except Bluetooth

Run the main app in Docker, but when you need to print to Niimbot:
1. Temporarily run the script above
2. Print your labels
3. Stop it and go back to Docker

### Option 3: Advanced Docker Setup (Experimental)

If you really want to try Docker + Bluetooth, here are additional things to try:

#### A. Use Host Network Mode (Already Done)
```yaml
network_mode: host
```

#### B. Pass Bluetooth Devices (Already Done)
```yaml
devices:
  - /dev/bus/usb:/dev/bus/usb
volumes:
  - /var/run/dbus:/var/run/dbus
  - /run/dbus:/run/dbus
  - /sys/class/bluetooth:/sys/class/bluetooth
```

#### C. Try Running bluetoothd Inside Container

Add to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    bluez \
    bluetooth \
    dbus \
    && rm -rf /var/lib/apt/lists/*
```

Add to docker-compose.yml:
```yaml
command: >
  sh -c "service dbus start &&
         bluetoothctl power on &&
         python run.py"
```

#### D. Use --net=host on Docker Run

If using `docker run` instead of compose:
```bash
docker run --privileged --net=host \
  -v /var/run/dbus:/var/run/dbus \
  -v /sys/class/bluetooth:/sys/class/bluetooth \
  your-image
```

## Current Status

Your setup has:
- ✅ Bluetooth tools installed in container
- ✅ Privileged mode enabled
- ✅ D-Bus volumes mounted
- ✅ Host network mode
- ✅ USB devices passed through
- ✅ Discovery working (finds printers)
- ❌ Connection failing (BLE connection issue)

The discovery works because it uses BLE scanning which is less restrictive. The actual connection requires deeper Bluetooth stack access that Docker typically can't provide reliably.

## Recommendation

**Use `./run_with_bluetooth.sh` for Niimbot printing.**

This gives you:
- 100% reliable Bluetooth connections
- Same application functionality
- Easy to switch back to Docker when done
- No complex Docker configuration needed

## For Production

If you need Bluetooth in production:
1. Run the app directly on the host (not in Docker)
2. Use a reverse proxy (nginx) for web access
3. Set up as a systemd service for auto-start

Example systemd service:
```ini
[Unit]
Description=Flask App with Bluetooth
After=network.target bluetooth.target

[Service]
Type=simple
User=an0naman
WorkingDirectory=/home/an0naman/Documents/GitHub/template
ExecStart=/home/an0naman/Documents/GitHub/template/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Quick Start

```bash
# Use this for Niimbot printing:
./run_with_bluetooth.sh

# Use this for everything else:
docker compose up -d
```

Both methods give you the same application at `http://localhost:5001`.
