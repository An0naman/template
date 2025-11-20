# CasaOS Compatibility Update

## ✅ Changes Made to Framework Template

The `app-instance-template/docker-compose.yml` has been updated for **CasaOS compatibility** by default.

### What Changed

#### 1. Network Mode
**Before:**
```yaml
network_mode: host
# ports:
#   - "${PORT:-5001}:5001"
```

**After:**
```yaml
# network_mode: host  # Commented out (use for Bluetooth)
ports:
  - "${PORT:-5001}:${PORT:-5001}"  # Active by default
```

#### 2. PORT Environment Variable
**Before:**
```yaml
environment:
  - PORT=5001  # Hardcoded
```

**After:**
```yaml
environment:
  - PORT=${PORT:-5001}  # Uses .env variable
```

#### 3. Health Check
**Before:**
```yaml
test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:5001/api/health', timeout=5)"]
```

**After:**
```yaml
test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:${PORT:-5001}/api/health', timeout=5)"]
```

## 🎯 Benefits

1. **CasaOS Compatible**: Apps are accessible from CasaOS web UI out of the box
2. **Network Accessible**: Apps work from any device on the network
3. **Dynamic Ports**: Each app can use its own port (5001, 5002, 5003, etc.)
4. **Docker Best Practices**: Bridge networking is the Docker standard

## ⚠️ Bluetooth Note

If you need **full Bluetooth support** for Niimbot printers:

1. Uncomment `network_mode: host` in docker-compose.yml
2. Comment out the `ports:` section
3. Access only via localhost on the server

**Trade-off**: Host mode = Bluetooth works, but not accessible from CasaOS remotely

## 📝 Tested Apps

Both apps created and verified working with updated template:

- **DevOps** (port 5002) - ✅ Accessible from network
- **Projects** (port 5003) - ✅ Accessible from network

Both apps:
- Start successfully
- Pass health checks
- Accessible from http://192.168.68.107:PORT
- Work with CasaOS web interface

## 🚀 Future App Instances

All new apps created from the template will now:
1. Use bridge networking by default
2. Be CasaOS compatible immediately
3. Work on any device on your network
4. No manual docker-compose.yml editing required

Date: October 29, 2025
