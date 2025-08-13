#!/usr/bin/env python3
"""
Diagnostic script for sensor alarm notifications

This script helps troubleshoot why sensor alarm notifications aren't being created.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://192.168.68.104:5001"

def diagnose_sensor_notifications():
    """Comprehensive diagnosis of sensor notification system"""
    print("🔍 Sensor Notification Diagnostic Tool")
    print("=" * 60)
    
    # Step 1: Check for devices and their sensor mappings
    print("\n1️⃣ Checking registered devices and sensor mappings...")
    response = requests.get(f"{BASE_URL}/api/devices")
    if response.status_code == 200:
        devices = response.json()
        print(f"Found {len(devices)} registered devices:")
        
        for device in devices:
            print(f"\n📱 Device: {device['device_name']} (ID: {device['id']})")
            print(f"   Status: {device['status']}")
            print(f"   Polling enabled: {device.get('polling_enabled', False)}")
            
            # Check sensor mappings for this device
            response = requests.get(f"{BASE_URL}/api/devices/{device['id']}/sensor-mappings")
            if response.status_code == 200:
                mapping_data = response.json()
                mappings = mapping_data.get('sensor_mappings', [])
                print(f"   Configured data points: {len(mappings)}")
                
                for mapping in mappings:
                    if mapping.get('enabled', False):
                        print(f"     ✅ {mapping['sensor_name']} → {mapping['entry_field']}")
                    else:
                        print(f"     ❌ {mapping['sensor_name']} → {mapping['entry_field']} (disabled)")
            else:
                print("   ❌ Could not fetch sensor mappings")
    else:
        print("❌ Could not fetch devices")
        return
    
    # Step 2: Check notification rules
    print("\n2️⃣ Checking notification rules (sensor alarms)...")
    response = requests.get(f"{BASE_URL}/api/notifications/rules")
    if response.status_code == 200:
        rules = response.json()
        print(f"Found {len(rules)} notification rules:")
        
        active_sensor_rules = []
        for rule in rules:
            if rule.get('is_active') and rule.get('sensor_type'):
                active_sensor_rules.append(rule)
                print(f"\n🚨 Rule ID {rule['id']}: {rule.get('notification_title', 'Untitled')}")
                print(f"   Sensor type: {rule['sensor_type']}")
                print(f"   Condition: {rule['condition_type']} {rule['threshold_value']}")
                print(f"   Priority: {rule.get('priority', 'medium')}")
                print(f"   Cooldown: {rule.get('cooldown_minutes', 0)} minutes")
                
                # Check if there are entries for this rule
                if rule.get('entry_id'):
                    print(f"   Applies to entry: {rule['entry_id']}")
                else:
                    print(f"   Applies to all entries")
        
        if not active_sensor_rules:
            print("❌ No active sensor-based notification rules found!")
            print("   Create a sensor alarm rule in the Manage Sensor Alarms page")
    else:
        print("❌ Could not fetch notification rules")
    
    # Step 3: Check recent sensor data
    print("\n3️⃣ Checking recent sensor data...")
    response = requests.get(f"{BASE_URL}/api/sensor_data?limit=10")
    if response.status_code == 200:
        sensor_data = response.json()
        print(f"Found {len(sensor_data)} recent sensor data points:")
        
        for data in sensor_data[-5:]:  # Show last 5
            print(f"   📊 Entry {data['entry_id']}: {data['sensor_type']} = {data['value']} at {data['recorded_at']}")
    else:
        print("❌ Could not fetch sensor data")
    
    # Step 4: Check existing notifications
    print("\n4️⃣ Checking existing notifications...")
    response = requests.get(f"{BASE_URL}/api/notifications")
    if response.status_code == 200:
        notifications = response.json()
        sensor_notifications = [n for n in notifications if n.get('notification_type') == 'sensor_based']
        print(f"Found {len(sensor_notifications)} sensor-based notifications:")
        
        for notif in sensor_notifications[-3:]:  # Show last 3
            print(f"   🔔 {notif.get('title', 'Untitled')}: {notif.get('message', 'No message')}")
            print(f"      Created: {notif.get('created_at', 'Unknown')}")
            print(f"      Dismissed: {notif.get('is_dismissed', False)}")
    else:
        print("❌ Could not fetch notifications")
    
    # Step 5: Test sensor rule checking manually
    print("\n5️⃣ Manual sensor rule test...")
    if 'active_sensor_rules' in locals() and active_sensor_rules and 'sensor_data' in locals() and sensor_data:
        rule = active_sensor_rules[0]
        recent_data = sensor_data[0] if sensor_data else None
        
        if recent_data:
            print(f"Testing rule '{rule.get('notification_title')}' against recent data:")
            print(f"   Rule sensor type: {rule['sensor_type']}")
            print(f"   Data sensor type: {recent_data['sensor_type']}")
            print(f"   Rule condition: {rule['condition_type']} {rule['threshold_value']}")
            print(f"   Data value: {recent_data['value']}")
            
            # Check if sensor types match
            if rule['sensor_type'] == recent_data['sensor_type']:
                print("   ✅ Sensor types match")
                
                # Try to extract numeric value
                try:
                    # Remove units and convert to float
                    numeric_value = float(''.join(c for c in recent_data['value'] if c.isdigit() or c == '.' or c == '-'))
                    threshold = rule['threshold_value']
                    
                    print(f"   Numeric value: {numeric_value}")
                    print(f"   Threshold: {threshold}")
                    
                    # Check condition
                    condition_met = False
                    if rule['condition_type'] == 'greater_than':
                        condition_met = numeric_value > threshold
                    elif rule['condition_type'] == 'less_than':
                        condition_met = numeric_value < threshold
                    elif rule['condition_type'] == 'equals':
                        condition_met = abs(numeric_value - threshold) < 0.01
                    
                    if condition_met:
                        print("   🚨 CONDITION MET - notification should be created!")
                    else:
                        print("   ℹ️  Condition not met - no notification expected")
                        
                except ValueError:
                    print(f"   ❌ Could not parse numeric value from: {recent_data['value']}")
            else:
                print("   ❌ Sensor types don't match - this is likely the problem!")
                print("   Check that your sensor mappings create the correct sensor type names")
    
    # Diagnosis summary
    print("\n" + "=" * 60)
    print("🏁 Diagnosis Summary")
    print("=" * 60)
    
    print("\n✅ Things to check:")
    print("1. Are your devices configured with data point mappings?")
    print("2. Do the sensor types in your alarm rules match the data point names?")
    print("3. Is device polling enabled and working?")
    print("4. Are your notification rules active?")
    print("5. Has the cooldown period passed since the last notification?")
    
    print("\n🔧 Common issues:")
    print("- Sensor type mismatch: Alarm for 'Temperature' but data stored as 'temp'")
    print("- No data point mappings configured for the device")
    print("- Device polling disabled or failing")
    print("- Notification rule condition never met")
    print("- Still in cooldown period from previous notification")
    
    print("\n💡 Next steps:")
    print("1. Configure data points in Manage Devices → Configure Data Points")
    print("2. Ensure alarm sensor type matches the data point field name exactly")
    print("3. Test manual device polling to generate fresh sensor data")
    print("4. Check application logs for any error messages")

if __name__ == "__main__":
    try:
        diagnose_sensor_notifications()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application. Please ensure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Diagnostic failed with error: {e}")
        print("\nThis might indicate a deeper issue with the application.")
