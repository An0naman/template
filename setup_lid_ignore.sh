#!/bin/bash

# This script configures a Linux laptop to stay awake when the lid is closed.
# It uses systemd drop-in files for persistence and masks sleep targets.

echo "1. Configuring systemd-logind via drop-in file (persists across updates)..."

# Create the drop-in directory if it doesn't exist
sudo mkdir -p /etc/systemd/logind.conf.d/

# Create a dedicated configuration file. 
# Using a drop-in file (ending in .conf) in this directory overrides the main config 
# and is not overwritten when the systemd package is updated.
cat <<EOF | sudo tee /etc/systemd/logind.conf.d/99-lid-ignore.conf
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
EOF

echo "2. Masking sleep targets to prevent suspension entirely..."
# This prevents the system from sleeping, hibernating, or suspending manually or automatically.
# This is the strongest guarantee that the server won't go to sleep.
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

echo "3. Restarting systemd-logind to apply changes..."
sudo systemctl restart systemd-logind

echo "4. Disabling WiFi Power Management (prevents network drops)..."
# Create a NetworkManager configuration to disable power saving for WiFi
# This is more persistent than using iwconfig directly
cat <<EOF | sudo tee /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf
[connection]
wifi.powersave=2
EOF
# Reload NetworkManager to apply
sudo systemctl reload NetworkManager

echo "Configuration complete."
echo "- Created /etc/systemd/logind.conf.d/99-lid-ignore.conf"
echo "- Masked sleep, suspend, hibernate, and hybrid-sleep targets"
echo "- Disabled WiFi power management via NetworkManager"
echo ""
echo "IMPORTANT NOTES:"
echo "1. COOLING: Ensure your laptop vents are not blocked. Some laptops vent through the keyboard,"
echo "   so running with the lid closed can cause overheating. Monitor temperatures initially."
echo "2. DESKTOP ENV: You are running XFCE. If the screen locks or goes blank, that is normal/good."
echo "   If you want to prevent screen locking, check XFCE Power Manager settings,"
echo "   but the system itself will NOT sleep."
echo ""
echo "Your laptop server should now be unable to sleep or suspend."
