#!/usr/bin/env python3
"""
Test script to specifically check entry 2 alarm functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://192.168.68.104:5001"

def test_entry_2_alarms():
    print("🧪 Testing Entry 2 Alarm Functionality")
    print("=" * 60)
    
    # 1. Check which devices are linked to entry 2
    print("\n1️⃣ Checking device links for entry 2...")
    try:
        response = requests.get(f'{BASE_URL}/api/devices')
        devices = response.json()
        
        linked_device = None
        for device in devices:
            # Handle different formats for linked_entries
            linked_entries = device.get('linked_entries', [])
            linked_ids = []
            
            try:
                if isinstance(linked_entries, str):
                    # String format: "1,2,3"
                    linked_ids = [int(x.strip()) for x in linked_entries.split(',') if x.strip()]
                elif isinstance(linked_entries, list):
                    # List format: could be [1,2,3] or ["1","2","3"] or [{"id":1}, {"id":2}]
                    for item in linked_entries:
                        if isinstance(item, dict):
                            # Handle dict format: {"id": 1}
                            if 'id' in item:
                                linked_ids.append(int(item['id']))
                            elif 'entry_id' in item:
                                linked_ids.append(int(item['entry_id']))
                        else:
                            # Handle direct number or string
                            linked_ids.append(int(item))
                else:
                    linked_ids = []
            except Exception as e:
                print(f"   Warning: Could not parse linked_entries for device {device.get('id')}: {e}")
                print(f"   Raw linked_entries: {linked_entries}")
                continue
                
            if 2 in linked_ids:
                linked_device = device
                print(f'✅ Entry 2 is linked to Device {device["id"]} ({device["device_name"]})')
                print(f'   - Auto-polling: {"Enabled" if device.get("polling_enabled") else "Disabled"}')
                print(f'   - Polling interval: {device.get("polling_interval", "Unknown")} seconds')
                print(f'   - Last seen: {device.get("last_seen", "Never")}')
                print(f'   - Status: {device.get("status", "Unknown")}')
                break
        
        if not linked_device:
            print('❌ Entry 2 is not linked to any device!')
            return
            
    except Exception as e:
        print(f'❌ Error checking devices: {e}')
        return

    device_id = linked_device['id']
    
    # 2. Check the alarm rule details
    print(f'\n2️⃣ Checking alarm rule details...')
    try:
        response = requests.get(f'{BASE_URL}/api/notification_rules')
        if response.status_code == 200:
            rules = response.json()
            applicable_rule = None
            for rule in rules:
                if (rule.get('name') == 'TESTq' and 
                    rule.get('sensor_type') == 'Free Memory' and 
                    rule.get('is_active')):
                    applicable_rule = rule
                    break
            
            if applicable_rule:
                print(f'✅ Found applicable alarm rule:')
                print(f'   - Name: {applicable_rule["name"]}')
                print(f'   - Sensor: {applicable_rule["sensor_type"]}')
                print(f'   - Condition: {applicable_rule["condition_type"]} {applicable_rule["threshold_value"]}')
                print(f'   - Scope: Entry Type {applicable_rule.get("entry_type_id")}')
                print(f'   - Cooldown: {applicable_rule.get("cooldown_minutes", 60)} minutes')
                print(f'   - Active: {applicable_rule["is_active"]}')
            else:
                print('❌ Could not find the TESTq alarm rule')
                return
        else:
            print(f'❌ Failed to get alarm rules: {response.status_code}')
            return
    except Exception as e:
        print(f'❌ Error checking alarm rules: {e}')
        return

    # 3. Check current sensor data by manually polling the device
    print(f'\n3️⃣ Getting current sensor data for device {device_id}...')
    try:
        response = requests.post(f'{BASE_URL}/api/devices/{device_id}/poll')
        if response.status_code == 200:
            result = response.json()
            device_data = result.get('device_data', {})
            
            if 'system' in device_data and 'free_heap' in device_data['system']:
                free_heap = device_data['system']['free_heap']
                threshold = applicable_rule['threshold_value']
                
                print(f'✅ Current Free Memory: {free_heap:,} bytes')
                print(f'🎯 Alarm threshold: {threshold:,} bytes')
                
                should_trigger = free_heap < threshold
                print(f'🚨 Should trigger alarm: {should_trigger}')
                
                if should_trigger:
                    print(f'   ✅ Condition met: {free_heap:,} < {threshold:,}')
                else:
                    print(f'   ❌ Condition not met: {free_heap:,} >= {threshold:,}')
            else:
                print('❌ No Free Memory data found in device response')
                print(f'Device data keys: {list(device_data.keys())}')
        else:
            print(f'❌ Failed to poll device: {response.status_code} - {response.text}')
            return
    except Exception as e:
        print(f'❌ Error polling device: {e}')
        return

    # 4. Check existing notifications for entry 2
    print(f'\n4️⃣ Checking existing notifications for entry 2...')
    try:
        response = requests.get(f'{BASE_URL}/api/notifications?entry_id=2')
        if response.status_code == 200:
            notifications = response.json()
            sensor_notifications = [n for n in notifications if n.get('notification_type') == 'sensor_based']
            
            print(f'📬 Found {len(notifications)} total notifications for entry 2')
            print(f'🚨 Found {len(sensor_notifications)} sensor-based notifications for entry 2')
            
            if sensor_notifications:
                print('Recent sensor notifications:')
                for notif in sorted(sensor_notifications, key=lambda x: x.get('created_at', ''), reverse=True)[:3]:
                    print(f'   🔔 {notif.get("created_at", "unknown")}: {notif.get("title", "No title")}')
                    print(f'      Priority: {notif.get("priority", "unknown")}')
        else:
            print(f'❌ Failed to get notifications: {response.status_code}')
    except Exception as e:
        print(f'❌ Error checking notifications: {e}')

    # 5. Check cooldown period
    print(f'\n5️⃣ Checking cooldown period...')
    try:
        response = requests.get(f'{BASE_URL}/api/notifications')
        if response.status_code == 200:
            all_notifications = response.json()
            
            # Find last sensor notification for entry 2
            entry_2_sensor_notifs = [
                n for n in all_notifications 
                if (n.get('notification_type') == 'sensor_based' and 
                    n.get('entry_id') == 2)
            ]
            
            if entry_2_sensor_notifs:
                last_notif = max(entry_2_sensor_notifs, key=lambda x: x.get('created_at', ''))
                last_time = last_notif.get('created_at', '')
                cooldown_minutes = applicable_rule.get('cooldown_minutes', 60)
                
                print(f'⏰ Last sensor notification: {last_time}')
                print(f'🕐 Cooldown period: {cooldown_minutes} minutes')
                
                # Calculate if we're still in cooldown
                try:
                    from datetime import datetime, timedelta
                    last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                    cooldown_end = last_dt + timedelta(minutes=cooldown_minutes)
                    now = datetime.now(last_dt.tzinfo) if last_dt.tzinfo else datetime.now()
                    
                    in_cooldown = now < cooldown_end
                    print(f'🚦 Currently in cooldown: {in_cooldown}')
                    
                    if in_cooldown:
                        remaining = cooldown_end - now
                        print(f'   ⏳ Time remaining: {remaining}')
                except Exception as e:
                    print(f'   ❌ Error calculating cooldown: {e}')
            else:
                print('✅ No previous sensor notifications found - no cooldown period')
                
    except Exception as e:
        print(f'❌ Error checking cooldown: {e}')

    # 6. Summary and recommendations
    print(f'\n' + '=' * 60)
    print(f'📋 SUMMARY FOR ENTRY 2:')
    print(f'✅ Entry 2 is linked to Device {device_id}')
    print(f'✅ Device has auto-polling enabled: {linked_device.get("polling_enabled", False)}')
    print(f'✅ Active alarm rule exists for Free Memory < 50M bytes')
    
    if 'should_trigger' in locals():
        print(f'{"✅" if should_trigger else "❌"} Current condition {"MEETS" if should_trigger else "does NOT meet"} alarm threshold')
    
    if 'sensor_notifications' in locals():
        print(f'📬 Current sensor notifications for entry 2: {len(sensor_notifications)}')
    
    print(f'\n💡 EXPECTED BEHAVIOR:')
    if 'should_trigger' in locals() and should_trigger:
        print(f'   🚨 Entry 2 SHOULD receive alarm notifications when auto-polling runs')
        print(f'   ⏰ Unless it\'s in the cooldown period from a recent notification')
    else:
        print(f'   ✅ Entry 2 should NOT receive alarm notifications (condition not met)')

if __name__ == "__main__":
    try:
        test_entry_2_alarms()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
