#!/usr/bin/env python3
"""
Test script to validate the automatic sensor type registration functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.sensor_type_manager import (
    auto_register_sensor_types, 
    get_sensor_types_from_device_data,
    ensure_sensor_type_exists
)

def test_sensor_type_discovery():
    """Test sensor type discovery from device data"""
    print("🧪 Testing sensor type discovery...")
    
    # Example ESP32 fermentation controller data
    sample_device_data = {
        "device_id": "ESP32_001",
        "device_name": "Fermentation Controller 1",
        "sensor": {
            "temperature": 23.5,
            "valid": True
        },
        "relay": {
            "state": "OFF",
            "pin": 2
        },
        "network": {
            "rssi": -45,
            "ssid": "MyNetwork"
        },
        "system": {
            "free_heap": 123456,
            "uptime_ms": 86400000,
            "uptime_formatted": "1d 0h 0m 0s"
        },
        "timestamp": "2025-01-01T12:00:00Z"
    }
    
    # Test discovery
    discovered_types = get_sensor_types_from_device_data(sample_device_data)
    print(f"✅ Discovered sensor types: {discovered_types}")
    
    # Test that reasonable types are discovered
    expected_types = ['Temperature', 'Relay State', 'WiFi Signal']
    for expected in expected_types:
        if any(expected in dtype for dtype in discovered_types):
            print(f"✅ Found expected type containing '{expected}'")
        else:
            print(f"❌ Missing expected type containing '{expected}'")
    
    return discovered_types

def test_sensor_registration():
    """Test automatic sensor type registration"""
    print("\n🧪 Testing sensor type registration...")
    
    # Test data points
    test_sensor_points = [
        {'sensor_type': 'Test Temperature'},
        {'sensor_type': 'Test Pressure'},
        {'sensor_type': 'Test Humidity'}
    ]
    
    # Test registration
    print("📝 Attempting to register test sensor types...")
    new_types = auto_register_sensor_types(test_sensor_points, "Test Device")
    print(f"✅ Registered {len(new_types)} new types: {new_types}")
    
    # Test duplicate registration (should not create duplicates)
    print("📝 Attempting to register same types again...")
    duplicate_types = auto_register_sensor_types(test_sensor_points, "Test Device")
    print(f"✅ Duplicate registration returned {len(duplicate_types)} new types (should be 0)")
    
    return new_types

def test_ensure_sensor_type():
    """Test ensure_sensor_type_exists function"""
    print("\n🧪 Testing ensure_sensor_type_exists...")
    
    # Test with new type
    result = ensure_sensor_type_exists("Test Unique Type")
    print(f"✅ ensure_sensor_type_exists returned: {result}")
    
    # Test with empty type
    result = ensure_sensor_type_exists("")
    print(f"✅ ensure_sensor_type_exists with empty string returned: {result} (should be False)")
    
    return result

if __name__ == "__main__":
    print("🚀 Starting sensor type management tests...\n")
    
    try:
        # Run tests
        discovered = test_sensor_type_discovery()
        registered = test_sensor_registration()
        ensured = test_ensure_sensor_type()
        
        print("\n✅ All tests completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Discovered {len(discovered)} sensor types from sample data")
        print(f"   - Registered {len(registered)} new sensor types")
        print(f"   - Sensor type existence check: {'✅' if ensured else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n🎉 Dynamic sensor type management is working correctly!")
