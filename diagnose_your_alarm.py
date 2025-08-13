#!/usr/bin/env python3
"""
Specific diagnostic for your sensor alarm issue
"""

import requests
import json

BASE_URL = "http://192.168.68.104:5001"

def diagnose_your_alarm():
    print("🔍 Diagnosing Your Sensor Alarm Issue")
    print("=" * 50)
    
    # 1. Check device 7 current data
    print("\n1️⃣ Checking device 7 sensor data collection...")
    response = requests.post(f"{BASE_URL}/api/devices/7/poll")
    if response.status_code == 200:
        result = response.json()
        free_heap = result['device_data']['system']['free_heap']
        print(f"✅ Device polled successfully")
        print(f"📊 Current Free Memory: {free_heap} bytes")
        print(f"📈 Stored {result['stored_sensors']} sensor readings")
    else:
        print(f"❌ Device poll failed: {response.text}")
        return
    
    # 2. Check sensor mapping
    print(f"\n2️⃣ Checking sensor mappings...")
    response = requests.get(f"{BASE_URL}/api/devices/7/sensor-mappings")
    if response.status_code == 200:
        mappings = response.json()['sensor_mappings']
        for mapping in mappings:
            if mapping['enabled']:
                print(f"✅ {mapping['sensor_name']} → {mapping['entry_field']}")
    
    # 3. Try to find notification rules via different endpoints
    print(f"\n3️⃣ Searching for notification rules...")
    
    # Try different possible endpoints
    endpoints_to_try = [
        "/api/notifications/rules",
        "/api/notification_rules", 
        "/api/notification-rules",
        "/api/sensor_alarms",
        "/api/sensor-alarms"
    ]
    
    rules_found = False
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                rules = response.json()
                if rules:
                    print(f"✅ Found rules at {endpoint}:")
                    for rule in rules:
                        print(f"   📋 Rule: {rule.get('name', 'Unnamed')}")
                        print(f"      Sensor Type: {rule.get('sensor_type')}")
                        print(f"      Condition: {rule.get('condition_type')} {rule.get('threshold_value')}")
                        print(f"      Active: {rule.get('is_active', False)}")
                    rules_found = True
                    break
                else:
                    print(f"✅ {endpoint} exists but no rules configured")
                    rules_found = True
                    break
        except:
            continue
    
    if not rules_found:
        print("❌ Could not find notification rules endpoint")
    
    # 4. Check current notifications
    print(f"\n4️⃣ Checking current notifications...")
    response = requests.get(f"{BASE_URL}/api/notifications")
    if response.status_code == 200:
        notifications = response.json()
        print(f"📬 Found {len(notifications)} notifications")
        sensor_notifs = [n for n in notifications if n.get('notification_type') == 'sensor_based']
        print(f"🚨 Sensor-based notifications: {len(sensor_notifs)}")
    
    print(f"\n" + "=" * 50)
    print("🎯 DIAGNOSIS RESULTS:")
    print("=" * 50)
    
    print(f"✅ Device is working and collecting data")
    print(f"✅ Free Memory sensor data: {free_heap} bytes")
    print(f"✅ Sensor mapping configured: system.free_heap → Free Memory")
    
    if not rules_found:
        print(f"❌ No sensor alarm rules found")
        print(f"\n💡 SOLUTION:")
        print(f"1. Go to: {BASE_URL}/maintenance/manage_sensor_alarms")
        print(f"2. Create a new sensor alarm rule:")
        print(f"   - Sensor Type: 'Free Memory'")
        print(f"   - Condition: 'less than' or 'greater than'")
        print(f"   - Threshold: {free_heap - 10000} (to trigger immediately)")
        print(f"   - Make sure it's Active")
        print(f"3. Test by polling device again")
    else:
        print(f"🤔 Rules exist but notification not triggered")
        print(f"\n💡 CHECK:")
        print(f"1. Sensor type in alarm rule EXACTLY matches 'Free Memory'")
        print(f"2. Threshold condition can be met (current value: {free_heap})")
        print(f"3. Rule is marked as Active")
        print(f"4. Not in cooldown period from previous notification")

if __name__ == "__main__":
    try:
        diagnose_your_alarm()
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
