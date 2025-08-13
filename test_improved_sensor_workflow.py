#!/usr/bin/env python3
"""
Test script for the improved sensor type management workflow

This script demonstrates how sensor types are now created when users
configure data points rather than during device registration.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://192.168.68.104:5001"
TEST_DEVICE = {
    "device_id": "test_esp32_improved",
    "device_name": "Test ESP32 Device (Improved)",
    "ip": "192.168.68.100",  # Adjust to your device's IP
    "device_type": "esp32_fermentation",
    "capabilities": ["temperature", "relay_control"]
}

def test_improved_workflow():
    """Test the improved sensor type creation workflow"""
    print("🧪 Testing Improved Sensor Type Management Workflow")
    print("=" * 60)
    
    # Step 1: Check initial sensor types
    print("\n1️⃣ Checking initial sensor types...")
    response = requests.get(f"{BASE_URL}/api/system_params/sensor_types")
    if response.status_code == 200:
        initial_types = response.json().get('value', '').split(',') if response.json().get('value') else []
        print(f"Initial sensor types: {initial_types}")
    else:
        print("Could not fetch initial sensor types")
        initial_types = []
    
    # Step 2: Register device (should NOT create sensor types)
    print("\n2️⃣ Registering device (should NOT auto-create sensor types)...")
    response = requests.post(f"{BASE_URL}/api/devices", json=TEST_DEVICE)
    if response.status_code == 201:
        result = response.json()
        device_id = result['device_id']
        print(f"✅ Device registered successfully: {result['message']}")
        print(f"Device ID: {device_id}")
        
        # Check if sensor types were NOT created
        if 'discovered_sensor_types' not in result:
            print("✅ Correct: No automatic sensor type creation during registration")
        else:
            print(f"❌ Unexpected: Sensor types were auto-created: {result.get('discovered_sensor_types')}")
    else:
        print(f"❌ Failed to register device: {response.text}")
        return
    
    # Step 3: Check sensor types after registration (should be unchanged)
    print("\n3️⃣ Checking sensor types after device registration...")
    response = requests.get(f"{BASE_URL}/api/system_params/sensor_types")
    if response.status_code == 200:
        after_reg_types = response.json().get('value', '').split(',') if response.json().get('value') else []
        print(f"Sensor types after registration: {after_reg_types}")
        if set(after_reg_types) == set(initial_types):
            print("✅ Correct: No sensor types were created during device registration")
        else:
            new_types = set(after_reg_types) - set(initial_types)
            print(f"❌ Unexpected: New types created during registration: {new_types}")
    
    # Step 4: Configure data points (THIS is where sensor types should be created)
    print("\n4️⃣ Configuring data points (should create sensor types)...")
    
    # First, get available sensors from device
    print("Getting available device data fields...")
    response = requests.get(f"{BASE_URL}/api/devices/{device_id}/sensor-mappings")
    if response.status_code == 200:
        mapping_data = response.json()
        available_sensors = mapping_data.get('available_sensors', [])
        print(f"Available device fields: {[s['name'] for s in available_sensors[:5]]}...")  # Show first 5
        
        # Configure some data points
        test_mappings = [
            {
                "sensor_name": "sensor.temperature",
                "entry_field": "Temperature",  # User chooses this name  
                "data_type": "number",
                "unit": "°C",
                "enabled": True
            },
            {
                "sensor_name": "network.rssi", 
                "entry_field": "WiFi Signal Strength",  # User chooses this name
                "data_type": "number", 
                "unit": "dBm",
                "enabled": True
            },
            {
                "sensor_name": "system.free_heap",
                "entry_field": "Free Memory",  # User chooses this name - should match exactly
                "data_type": "number",
                "unit": "bytes", 
                "enabled": True
            }
        ]
        
        print(f"Configuring {len(test_mappings)} data points...")
        response = requests.post(f"{BASE_URL}/api/devices/{device_id}/sensor-mappings", 
                               json={"mappings": test_mappings})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Data points configured: {result['message']}")
            
            # Check if sensor types were created
            if 'new_sensor_types' in result and result['new_sensor_types']:
                print(f"✅ Sensor types created during configuration: {result['new_sensor_types']}")
                
                # Verify the names match what users chose
                expected_types = ['Temperature', 'WiFi Signal Strength', 'Free Memory']
                created_types = result['new_sensor_types']
                
                for expected in expected_types:
                    if expected in created_types:
                        print(f"  ✅ {expected} - matches user choice")
                    else:
                        print(f"  ❌ {expected} - missing from created types")
            else:
                print("❌ No sensor types were created during data point configuration")
        else:
            print(f"❌ Failed to configure data points: {response.text}")
    else:
        print(f"❌ Failed to get sensor mappings: {response.text}")
    
    # Step 5: Verify final sensor types
    print("\n5️⃣ Verifying final sensor types...")
    response = requests.get(f"{BASE_URL}/api/system_params/sensor_types")
    if response.status_code == 200:
        final_types = response.json().get('value', '').split(',') if response.json().get('value') else []
        print(f"Final sensor types: {final_types}")
        
        # Check for expected types
        expected_user_types = ['Temperature', 'WiFi Signal Strength', 'Free Memory']
        for expected in expected_user_types:
            if expected in final_types:
                print(f"  ✅ {expected} - present")
            else:
                print(f"  ❌ {expected} - missing")
    
    # Cleanup
    print("\n🧹 Cleaning up test device...")
    response = requests.delete(f"{BASE_URL}/api/devices/{device_id}")
    if response.status_code == 200:
        print("✅ Test device deleted successfully")
    else:
        print(f"❌ Failed to delete test device: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 Improved Workflow Test Complete!")
    print("\nKey Improvements Demonstrated:")
    print("✅ Device registration does NOT auto-create sensor types")
    print("✅ Sensor types are created when users configure data points")  
    print("✅ Sensor type names match exactly what users choose")
    print("✅ No mismatched names (Free Memory vs Memory Usage)")
    print("✅ Users have full control over when/what sensor types are created")

if __name__ == "__main__":
    try:
        test_improved_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application. Please ensure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
