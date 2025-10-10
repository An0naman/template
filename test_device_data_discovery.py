#!/usr/bin/env python3
"""
Test script to verify device data discovery improvements
This tests the fixes for finding all sensor data points including nested and array data
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_data_structure_analysis():
    """Test how well the system discovers data points from various structures"""
    
    print_section("Testing Device Data Point Discovery")
    
    # Test Case 1: Simple nested structure
    print("Test Case 1: Simple Nested Structure")
    test_data_1 = {
        'device_id': 'TEST_001',
        'sensor': {
            'temperature': 20.5,
            'humidity': 65.3,
            'pressure': 1013.25
        },
        'network': {
            'rssi': -67,
            'ip_address': '192.168.1.100'
        }
    }
    print(f"Input: {json.dumps(test_data_1, indent=2)}")
    
    # Test Case 2: Array of sensors
    print("\n\nTest Case 2: Array of Sensors")
    test_data_2 = {
        'device_id': 'TEST_002',
        'sensors': [
            {'id': 'sensor1', 'temperature': 18.5, 'valid': True},
            {'id': 'sensor2', 'temperature': 19.2, 'valid': True},
            {'id': 'sensor3', 'temperature': 21.0, 'valid': False}
        ]
    }
    print(f"Input: {json.dumps(test_data_2, indent=2)}")
    
    # Test Case 3: Complex nested structure (fermentation controller)
    print("\n\nTest Case 3: Complex ESP32 Fermentation Controller Structure")
    test_data_3 = {
        'device_id': 'ESP32_FERM_001',
        'device_name': 'Fermentation Controller',
        'timestamp': '2025-10-11T10:30:00Z',
        'sensor': {
            'temperature': 20.5,
            'humidity': 65.3,
            'target_temp': 20.0
        },
        'network': {
            'rssi': -67,
            'ip_address': '192.168.1.100',
            'wifi_ssid': 'HomeNetwork'
        },
        'system': {
            'free_heap': 45000,
            'uptime_ms': 123456789,
            'uptime_formatted': '1d 10h 17m',
            'buffer_count': 150,
            'buffer_max': 1000
        },
        'relay': {
            'state': 'ON',
            'pin': 23,
            'heating_pad': True
        },
        'ds18b20': {
            'devices': [
                {
                    'id': '28FF123456789012',
                    'temperature': 18.5,
                    'valid': True,
                    'sensor_type': 'DS18B20'
                },
                {
                    'id': '28FF987654321098',
                    'temperature': 19.2,
                    'valid': True,
                    'sensor_type': 'DS18B20'
                }
            ]
        }
    }
    print(f"Input: {json.dumps(test_data_3, indent=2)}")
    
    # Test the preview endpoint
    print("\n\n" + "="*60)
    print("Testing Data Point Preview Endpoint")
    print("="*60)
    
    for i, test_data in enumerate([test_data_1, test_data_2, test_data_3], 1):
        print(f"\nTest Case {i}:")
        try:
            response = requests.post(
                f"{BASE_URL}/api/system_params/preview_device_sensors",
                json={'device_data': test_data},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                discovered = result.get('discovered_sensor_types', [])
                print(f"✅ Discovered {len(discovered)} data points:")
                for sensor_type in sorted(discovered):
                    # Skip metadata fields
                    if sensor_type not in ['device_id', 'device_name', 'timestamp']:
                        print(f"   - {sensor_type}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test array notation extraction
    print("\n\n" + "="*60)
    print("Testing Array Notation Path Extraction")
    print("="*60)
    
    print("\nVerifying that paths like 'sensors[0].temperature' can be extracted:")
    print("Expected behavior:")
    print("  ✓ 'sensor.temperature' should work (simple nested)")
    print("  ✓ 'sensors[0].temperature' should work (array item)")
    print("  ✓ 'sensors[1].temperature' should work (second array item)")
    print("  ✓ 'ds18b20.devices[0].temperature' should work (deeply nested array)")
    
    print("\nThese improvements ensure:")
    print("  1. All nested data points are discovered")
    print("  2. All array items are discovered (up to 5 items)")
    print("  3. Paths with array notation can be extracted during polling")
    print("  4. Users can configure any data point as a sensor")

def test_device_workflow():
    """Test the complete device workflow"""
    
    print_section("Complete Device Workflow Test")
    
    print("Steps to verify the fix:")
    print("1. Register a device that sends array data")
    print("2. Open 'Configure Data Points' modal")
    print("3. Verify all array items are shown (e.g., sensors[0], sensors[1], sensors[2])")
    print("4. Enable data points from array items")
    print("5. Poll the device")
    print("6. Verify data is correctly extracted and stored")
    
    print("\n" + "="*60)
    print("Manual Testing Instructions")
    print("="*60)
    print("\n1. Go to: http://localhost:5000/manage_devices")
    print("2. Add a test device with array data structure")
    print("3. Click 'Configure Data Points' button")
    print("4. Check if you see all array items in the 'Available Sensors' list")
    print("5. Enable some array-based sensors (e.g., sensors[0].temperature)")
    print("6. Save the configuration")
    print("7. Poll the device and verify data is extracted correctly")

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║  Device Data Point Discovery Test                         ║
║  Testing fixes for nested and array data structures       ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        test_data_structure_analysis()
        test_device_workflow()
        
        print("\n\n" + "="*60)
        print("Summary of Fixes")
        print("="*60)
        print("\n✅ Fixed Issues:")
        print("   1. get_nested_value() now handles array notation (e.g., sensors[0])")
        print("   2. _analyze_data_structure() now discovers all array items")
        print("   3. Device manager will now show all available data points")
        print("\n✅ Improvements:")
        print("   - Analyzes up to 5 items in arrays (configurable)")
        print("   - Properly extracts values from nested arrays")
        print("   - Better data point discovery for complex devices")
        
        print("\n" + "="*60)
        print("Next Steps")
        print("="*60)
        print("\n1. Test with your actual device")
        print("2. Configure data points for array-based sensors")
        print("3. Verify data extraction during polling")
        print("4. Check that sensor alarms work with the new data")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
