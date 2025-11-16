#!/bin/bash
# Setup iptables rules to allow Tailscale VPN traffic to reach Docker containers
# This fixes the issue where downstream apps in bridge network mode are not accessible via Tailscale

echo "Setting up Tailscale → Docker forwarding rules..."

# Add rule to DOCKER-USER chain to accept traffic from tailscale0 interface
# Check if rule already exists
if sudo iptables -C DOCKER-USER -i tailscale0 -j ACCEPT 2>/dev/null; then
    echo "✅ Rule already exists"
else
    sudo iptables -I DOCKER-USER -i tailscale0 -j ACCEPT
    echo "✅ Added iptables rule: Allow tailscale0 → Docker containers"
fi

# Display current DOCKER-USER rules
echo ""
echo "Current DOCKER-USER chain rules:"
sudo iptables -L DOCKER-USER -n -v --line-numbers

echo ""
echo "✅ Tailscale VPN traffic can now reach Docker containers in bridge mode"
echo ""
echo "⚠️  NOTE: This rule will be lost on reboot unless made persistent."
echo "To make it persistent, you need to:"
echo "1. Install iptables-persistent: sudo apt install iptables-persistent"
echo "2. Save rules: sudo netfilter-persistent save"
echo "   OR manually add this script to run at boot (systemd service or cron @reboot)"

exit 0
