#!/usr/bin/env python3
"""
Test script for user preferences API
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_chart_preferences_api():
    """Test the chart preferences API endpoints"""
    entry_id = 22  # Using the entry ID from the logs
    
    print("Testing Chart Preferences API...")
    
    # Test 1: Get chart preferences (should return defaults)
    print("\n1. Getting initial chart preferences...")
    response = requests.get(f"{BASE_URL}/api/user_preferences/chart/{entry_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Set chart preferences
    print("\n2. Setting chart preferences...")
    test_preferences = {
        "chartType": "bar",
        "sensorType": "temperature",
        "timeRange": "24h",
        "dataLimit": "100"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/user_preferences/chart/{entry_id}",
        headers={"Content-Type": "application/json"},
        json=test_preferences
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Get chart preferences again (should return saved values)
    print("\n3. Getting saved chart preferences...")
    response = requests.get(f"{BASE_URL}/api/user_preferences/chart/{entry_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: Test general user preference
    print("\n4. Testing general user preference...")
    response = requests.post(
        f"{BASE_URL}/api/user_preferences/test_preference",
        headers={"Content-Type": "application/json"},
        json={"value": "test_value"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: Get the general preference
    print("\n5. Getting general preference...")
    response = requests.get(f"{BASE_URL}/api/user_preferences/test_preference")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 6: Delete chart preferences
    print("\n6. Deleting chart preferences...")
    response = requests.delete(f"{BASE_URL}/api/user_preferences/chart/{entry_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 7: Get chart preferences after deletion (should return defaults)
    print("\n7. Getting chart preferences after deletion...")
    response = requests.get(f"{BASE_URL}/api/user_preferences/chart/{entry_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    try:
        test_chart_preferences_api()
        print("\n✅ All tests completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the application. Make sure it's running on localhost:5001")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
