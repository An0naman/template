#!/bin/bash
#
# Setup Docker Network Forwarding Rules
# This script ensures all Docker bridge networks have proper iptables rules for internet access
# Run this after Docker starts or when creating new Docker networks
#

set -e

echo "🔧 Setting up Docker network forwarding rules..."

# Enable IP forwarding if not already enabled
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" != "1" ]; then
    echo "Enabling IP forwarding..."
    sysctl -w net.ipv4.ip_forward=1
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi

# Get all Docker bridge interfaces
# We use wildcards (br-+ and docker+) to handle current AND future networks
# This avoids the need to re-run the script when new networks are created

echo "Adding FORWARD rules for Docker bridges..."

# Allow traffic from/to docker bridges (br-*)
if ! iptables -C FORWARD -i br-+ -j ACCEPT 2>/dev/null; then
    iptables -I FORWARD 1 -i br-+ -j ACCEPT
    echo "✓ Added generic INPUT rule for br-+"
fi

if ! iptables -C FORWARD -o br-+ -j ACCEPT 2>/dev/null; then
    iptables -I FORWARD 1 -o br-+ -j ACCEPT
    echo "✓ Added generic OUTPUT rule for br-+"
fi

# Allow traffic from/to docker0 interface (docker+)
if ! iptables -C FORWARD -i docker+ -j ACCEPT 2>/dev/null; then
    iptables -I FORWARD 1 -i docker+ -j ACCEPT
    echo "✓ Added generic INPUT rule for docker+"
fi

if ! iptables -C FORWARD -o docker+ -j ACCEPT 2>/dev/null; then
    iptables -I FORWARD 1 -o docker+ -j ACCEPT
    echo "✓ Added generic OUTPUT rule for docker+"
fi

echo "Adding MASQUERADE rules for Docker subnets..."
# Add MASQUERADE rules for common Docker subnet ranges
for subnet in 172.{17..31}.0.0/16; do
    if ! iptables -t nat -C POSTROUTING -s $subnet ! -o docker0 -j MASQUERADE 2>/dev/null; then
        iptables -t nat -A POSTROUTING -s $subnet ! -o docker0 -j MASQUERADE
        echo "✓ Added MASQUERADE for $subnet"
    fi
done

# Also handle 10.x.x.x and 192.168.x.x ranges that Docker might use
for i in {0..255}; do
    subnet="10.${i}.0.0/16"
    if docker network ls --format '{{.Name}}' | xargs -I {} docker network inspect {} --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null | grep -q "^${subnet}$"; then
        if ! iptables -t nat -C POSTROUTING -s $subnet ! -o docker0 -j MASQUERADE 2>/dev/null; then
            iptables -t nat -A POSTROUTING -s $subnet ! -o docker0 -j MASQUERADE
            echo "✓ Added MASQUERADE for $subnet"
        fi
    fi
done

echo "✅ Docker network forwarding rules configured successfully!"
echo ""
echo "To make these rules persistent across reboots:"
echo "  1. Install iptables-persistent: sudo apt-get install iptables-persistent"
echo "  2. Save rules: sudo netfilter-persistent save"
echo "  OR"
echo "  3. Add this script to cron: @reboot /path/to/setup-docker-networking.sh"
