# Docker Networking Fix

## Problem

Docker containers in custom bridge networks may not have internet access due to missing iptables FORWARD rules. This particularly affects:
- API calls to external services (Google AI, GitHub, etc.)
- Package installations inside containers
- Any outbound network requests

## Root Cause

When Docker creates custom bridge networks, the host firewall's FORWARD chain (with DROP policy) can block traffic unless explicit ACCEPT rules exist for each bridge interface.

## Solution

### Quick Fix (Temporary - until reboot)

Run the setup script:
```bash
sudo /home/an0naman/Documents/GitHub/template/scripts/setup-docker-networking.sh
```

### Permanent Fix (Option 1: iptables-persistent)

1. Install iptables-persistent:
```bash
sudo apt-get update
sudo apt-get install iptables-persistent
```

2. Run the setup script:
```bash
sudo /home/an0naman/Documents/GitHub/template/scripts/setup-docker-networking.sh
```

3. Save the rules:
```bash
sudo netfilter-persistent save
```

The rules will now persist across reboots.

### Permanent Fix (Option 2: Systemd Service)

1. Copy the service file:
```bash
sudo cp /home/an0naman/Documents/GitHub/template/scripts/docker-networking.service /etc/systemd/system/
```

2. Update the script path in the service file if needed:
```bash
sudo nano /etc/systemd/system/docker-networking.service
# Update ExecStart path to absolute path of setup-docker-networking.sh
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable docker-networking.service
sudo systemctl start docker-networking.service
```

4. Check status:
```bash
sudo systemctl status docker-networking.service
```

## Testing

Test connectivity from any container:
```bash
# Test DNS resolution
docker exec <container-name> python3 -c "import socket; print(socket.gethostbyname('google.com'))"

# Test HTTP request
docker exec <container-name> python3 -c "import urllib.request; print(urllib.request.urlopen('https://google.com').status)"
```

## For New Docker Networks

When you create a new Docker Compose project (new network), run:
```bash
sudo /home/an0naman/Documents/GitHub/template/scripts/setup-docker-networking.sh
```

Or if using the systemd service:
```bash
sudo systemctl restart docker-networking.service
```

## Affected Applications

All applications using custom Docker bridge networks, including:
- devops (172.18.0.0/16)
- homebrews (172.19.0.0/16)
- sensor-master-control (172.20.0.0/16)
- template (172.21.0.0/16)
- garden-management (172.22.0.0/16)
- pickles-and-fermentation (172.23.0.0/16)
- hardware-build-and-design (172.24.0.0/16)
- 3d-printing (172.25.0.0/16)
- game-development (172.26.0.0/16)
- music-composition (172.27.0.0/16)
- cardputer (172.28.0.0/16)
- projects (172.29.0.0/16)

## Docker Compose Configuration

The template docker-compose files already include optimal DNS configuration:

```yaml
dns:
  - 8.8.8.8
  - 8.8.4.4
  - 1.1.1.1

dns_opt:
  - single-request
  - timeout:2
  - attempts:3

sysctls:
  net.ipv6.conf.all.disable_ipv6: "1"
  net.ipv6.conf.default.disable_ipv6: "1"
```

This ensures:
- Multiple DNS servers for redundancy
- Short timeouts to prevent hanging
- IPv6 disabled to avoid dual-stack issues

## Troubleshooting

### Check if forwarding is enabled:
```bash
cat /proc/sys/net/ipv4/ip_forward
# Should return 1
```

### Check FORWARD rules:
```bash
sudo iptables -L FORWARD -n
# Should show ACCEPT rules for Docker bridges
```

### Check MASQUERADE rules:
```bash
sudo iptables -t nat -L POSTROUTING -n
# Should show MASQUERADE rules for Docker subnets
```

### View logs:
```bash
# If using systemd service
sudo journalctl -u docker-networking.service -f
```

## Prevention for Future Apps

1. Always use the app-instance-template which includes proper DNS configuration
2. After creating a new app, test internet connectivity immediately
3. If connectivity fails, run the setup script
4. Consider using `network_mode: host` if you don't need network isolation

## Additional Notes

- The script is idempotent - safe to run multiple times
- Rules are applied in the correct order (FORWARD before DOCKER-USER)
- Handles all Docker subnet ranges (172.17-31.0.0/16, 10.x.0.0/16, etc.)
