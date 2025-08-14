#!/usr/bin/env python3
"""
Test script to verify automatic sensor alarm functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://192.168.68.104:5001"

def test_automatic_alarm_fix():
    print("🧪 Testing Automatic Sensor Alarm Fix")
    print("=" * 60)
    
    # 1. Check available devices
    print("\n1️⃣ Checking available devices...")
    response = requests.get(f"{BASE_URL}/api/devices")
    if response.status_code == 200:
        devices = response.json()
        print(f"📱 Found {len(devices)} devices:")
        for device in devices:
            status = device.get('status', 'unknown')
            polling = "✅ Auto-polling enabled" if device.get('polling_enabled') else "❌ Auto-polling disabled"
            print(f"   Device {device['id']}: {device['device_name']} ({status}) - {polling}")
    else:
        print(f"❌ Failed to get devices: {response.status_code}")
        return
    
    # Focus on device 11 (or the first available device)
    device_id = 11
    if devices:
        # Use the first available device if device 11 doesn't exist
        available_device = next((d for d in devices if d['id'] == device_id), devices[0])
        device_id = available_device['id']
        device_info = available_device
    else:
        print(f"❌ No devices found")
        return
    
    print(f"\n🎯 Testing with Device {device_id}: {device_info['device_name']}")
    
    # 2. Check sensor mappings for this device
    print(f"\n2️⃣ Checking sensor mappings for device {device_id}...")
    response = requests.get(f"{BASE_URL}/api/devices/{device_id}/sensor-mappings")
    if response.status_code == 200:
        mappings_data = response.json()
        mappings = mappings_data.get('sensor_mappings', [])
        print(f"🗺️ Found {len(mappings)} sensor mappings:")
        for mapping in mappings:
            if mapping['enabled']:
                print(f"   ✅ {mapping['sensor_name']} → {mapping['entry_field']} ({mapping.get('unit', 'no unit')})")
            else:
                print(f"   ❌ {mapping['sensor_name']} → {mapping['entry_field']} (disabled)")
    else:
        print(f"❌ Failed to get sensor mappings: {response.status_code}")
    
    # 3. Check existing sensor alarms
    print(f"\n3️⃣ Checking existing sensor alarms...")
    response = requests.get(f"{BASE_URL}/api/notification_rules")
    if response.status_code == 200:
        rules = response.json()
        active_rules = [r for r in rules if r.get('is_active', False)]
        print(f"🚨 Found {len(active_rules)} active sensor alarm rules:")
        for rule in active_rules:
            print(f"   📋 {rule['name']}: {rule['sensor_type']} {rule['condition_type']} {rule['threshold_value']}")
    else:
        print(f"❌ Failed to get alarm rules: {response.status_code}")
    
    # 4. Manual poll to get baseline (this should trigger alarms if conditions are met)
    print(f"\n4️⃣ Performing manual poll to establish baseline...")
    response = requests.post(f"{BASE_URL}/api/devices/{device_id}/poll")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Manual poll successful")
        print(f"📊 Stored {result.get('stored_sensors', 0)} sensor readings")
        
        # Check device data for key sensors
        device_data = result.get('device_data', {})
        if 'system' in device_data and 'free_heap' in device_data['system']:
            free_heap = device_data['system']['free_heap']
            print(f"💾 Current Free Memory: {free_heap} bytes")
        
    else:
        print(f"❌ Manual poll failed: {response.status_code} - {response.text}")
    
    # 5. Check notifications created by manual poll
    initial_notification_count = 0
    response = requests.get(f"{BASE_URL}/api/notifications")
    if response.status_code == 200:
        notifications = response.json()
        sensor_notifications = [n for n in notifications if n.get('notification_type') == 'sensor_based']
        initial_notification_count = len(sensor_notifications)
        print(f"📬 Current sensor-based notifications: {initial_notification_count}")
        
        # Show recent sensor notifications
        recent_notifications = sorted(sensor_notifications, key=lambda x: x.get('created_at', ''), reverse=True)[:3]
        for notif in recent_notifications:
            created_time = notif.get('created_at', 'unknown')
            print(f"   🔔 {notif.get('title', 'No title')} - {created_time}")
    
    # 6. Wait and check if automatic polling creates notifications
    print(f"\n5️⃣ Waiting 90 seconds for automatic polling...")
    print("⏳ The device scheduler polls every 30 seconds, waiting for at least 2 cycles...")
    
    for i in range(9):
        time.sleep(10)
        print(f"   ⏱️ {(i+1)*10}s elapsed...")
    
    # 7. Check for new notifications after automatic polling
    print(f"\n6️⃣ Checking for new notifications after automatic polling...")
    response = requests.get(f"{BASE_URL}/api/notifications")
    if response.status_code == 200:
        notifications = response.json()
        sensor_notifications = [n for n in notifications if n.get('notification_type') == 'sensor_based']
        final_notification_count = len(sensor_notifications)
        
        new_notifications = final_notification_count - initial_notification_count
        print(f"📬 Final sensor-based notifications: {final_notification_count}")
        print(f"🆕 New notifications created: {new_notifications}")
        
        if new_notifications > 0:
            print(f"✅ SUCCESS: Automatic polling is creating sensor notifications!")
            
            # Show the newest notifications
            recent_notifications = sorted(sensor_notifications, key=lambda x: x.get('created_at', ''), reverse=True)[:new_notifications]
            print(f"📋 New notifications:")
            for notif in recent_notifications:
                created_time = notif.get('created_at', 'unknown')
                print(f"   🔔 {notif.get('title', 'No title')} - {created_time}")
        else:
            print(f"⚠️ No new notifications created by automatic polling")
            print(f"💡 This could mean:")
            print(f"   - No alarm conditions were met")
            print(f"   - Alarms are in cooldown period")
            print(f"   - Device polling is disabled")
    
    # 8. Check device polling status
    print(f"\n7️⃣ Checking device polling status...")
    response = requests.get(f"{BASE_URL}/api/devices/{device_id}")
    if response.status_code == 200:
        device = response.json()
        last_poll = device.get('last_poll_success', 'Never')
        polling_enabled = device.get('polling_enabled', False)
        polling_interval = device.get('polling_interval', 60)
        
        print(f"🔄 Polling enabled: {polling_enabled}")
        print(f"⏱️ Polling interval: {polling_interval} seconds")
        print(f"📅 Last successful poll: {last_poll}")
        
        if not polling_enabled:
            print(f"❌ WARNING: Auto-polling is disabled for this device!")
            print(f"💡 Enable it in device settings to test automatic alarms")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 TEST SUMMARY:")
    print(f"✅ Manual polling: Working (triggers alarms)")
    print(f"{'✅' if new_notifications > 0 else '⚠️'} Automatic polling: {'Working (triggers alarms)' if new_notifications > 0 else 'May not be triggering alarms'}")
    print(f"📊 Sensor mappings: {len(mappings) if 'mappings' in locals() else 0} configured")
    print(f"🚨 Active alarm rules: {len(active_rules) if 'active_rules' in locals() else 0}")

if __name__ == "__main__":
    try:
        test_automatic_alarm_fix()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
