#!/usr/bin/env python3
"""
End-to-End Test for Sensor Data Module (Entry v2)
Tests the complete sensor section integration including:
- API endpoints
- Service layer helpers
- Frontend components
- CRUD operations
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

BASE_URL = "http://localhost:5000"
TEST_ENTRY_ID = None  # Will be set dynamically


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_test(name: str):
    """Print test name"""
    print(f"{Colors.OKBLUE}🧪 Testing: {name}{Colors.ENDC}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def test_entry_exists() -> bool:
    """Test that we have a valid entry to work with"""
    global TEST_ENTRY_ID
    print_test("Entry existence")
    
    try:
        # Try to get recent entries
        response = requests.get(f"{BASE_URL}/api/entries", timeout=5)
        if response.status_code == 200:
            entries = response.json()
            if isinstance(entries, list) and len(entries) > 0:
                TEST_ENTRY_ID = entries[0].get('id')
                print_success(f"Found test entry ID: {TEST_ENTRY_ID}")
                return True
        
        print_error("No entries found. Please create an entry first.")
        return False
    except Exception as e:
        print_error(f"Failed to fetch entries: {e}")
        return False


def test_sensor_types_endpoint() -> bool:
    """Test GET /api/entry/<entry_id>/sensor-types"""
    print_test("Sensor Types Endpoint")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/entry/{TEST_ENTRY_ID}/sensor-types",
            timeout=5
        )
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        # Validate response structure
        if 'sensor_types' not in data:
            print_error("Missing 'sensor_types' in response")
            return False
        
        if not isinstance(data['sensor_types'], list):
            print_error("'sensor_types' should be a list")
            return False
        
        print_success(f"Retrieved {len(data['sensor_types'])} sensor types")
        print(f"   Types: {', '.join(data['sensor_types'][:5])}")
        return True
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def test_create_sensor_reading() -> int:
    """Test POST /api/shared_sensor_data"""
    print_test("Create Sensor Reading")
    
    try:
        payload = {
            "sensor_type": "Temperature",
            "value": 22.5,
            "unit": "°C",
            "entry_ids": [TEST_ENTRY_ID],
            "recorded_at": datetime.utcnow().isoformat(),
            "source_type": "manual",
            "metadata": {"notes": "Test reading from E2E test"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shared_sensor_data",
            json=payload,
            timeout=5
        )
        
        if response.status_code not in [200, 201]:
            print_error(f"Expected 200/201, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
        
        data = response.json()
        sensor_id = data.get('id')
        
        if not sensor_id:
            print_error("No sensor ID in response")
            return None
        
        print_success(f"Created sensor reading with ID: {sensor_id}")
        return sensor_id
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return None


def test_get_sensor_data(sensor_id: int = None) -> bool:
    """Test GET /api/entry/<entry_id>/sensor-data"""
    print_test("Get Sensor Data")
    
    try:
        # Test without filters
        response = requests.get(
            f"{BASE_URL}/api/entry/{TEST_ENTRY_ID}/sensor-data",
            timeout=5
        )
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        if 'readings' not in data:
            print_error("Missing 'readings' in response")
            return False
        
        print_success(f"Retrieved {len(data['readings'])} readings")
        
        # Test with sensor_type filter
        response = requests.get(
            f"{BASE_URL}/api/entry/{TEST_ENTRY_ID}/sensor-data?sensor_type=Temperature",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Filtered by type: {len(data['readings'])} Temperature readings")
        
        # Test with statistics
        response = requests.get(
            f"{BASE_URL}/api/entry/{TEST_ENTRY_ID}/sensor-data?include_stats=true",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'statistics' in data:
                print_success("Statistics included in response")
                print(f"   Stats keys: {list(data['statistics'].keys())}")
            else:
                print_warning("Statistics requested but not in response")
        
        return True
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def test_update_sensor_reading(sensor_id: int) -> bool:
    """Test PUT /api/shared_sensor_data/<id>"""
    print_test("Update Sensor Reading")
    
    try:
        payload = {
            "value": 23.7,
            "unit": "°C",
            "metadata": {"notes": "Updated by E2E test"}
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shared_sensor_data/{sensor_id}",
            json=payload,
            timeout=5
        )
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
        
        print_success(f"Updated sensor reading {sensor_id}")
        return True
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def test_delete_sensor_reading(sensor_id: int) -> bool:
    """Test DELETE /api/shared_sensor_data/<id>"""
    print_test("Delete Sensor Reading")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/shared_sensor_data/{sensor_id}",
            timeout=5
        )
        
        if response.status_code not in [200, 204]:
            print_error(f"Expected 200/204, got {response.status_code}")
            return False
        
        print_success(f"Deleted sensor reading {sensor_id}")
        return True
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def test_time_range_filtering() -> bool:
    """Test time range filtering"""
    print_test("Time Range Filtering")
    
    try:
        # Test 24h range
        response = requests.get(
            f"{BASE_URL}/api/entry/{TEST_ENTRY_ID}/sensor-data",
            params={
                "start_date": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"24h range: {len(data['readings'])} readings")
        else:
            print_error(f"24h range failed: {response.status_code}")
            return False
        
        # Test 7d range
        response = requests.get(
            f"{BASE_URL}/api/entry/{TEST_ENTRY_ID}/sensor-data",
            params={
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"7d range: {len(data['readings'])} readings")
        else:
            print_error(f"7d range failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def test_frontend_page() -> bool:
    """Test that the Entry v2 page loads successfully"""
    print_test("Frontend Page Load")
    
    try:
        response = requests.get(
            f"{BASE_URL}/entry/{TEST_ENTRY_ID}/v2",
            timeout=10
        )
        
        if response.status_code != 200:
            print_error(f"Expected 200, got {response.status_code}")
            return False
        
        html = response.text
        
        # Check for key elements
        checks = {
            "Sensors section": 'id="sensorChart"' in html,
            "Sensor stats": 'id="sensorStats"' in html,
            "Sensor table": 'id="sensorDataTable"' in html,
            "Add modal": 'id="addSensorDataModal"' in html,
            "Edit modal": 'id="editSensorDataModal"' in html,
            "Static CSS": 'css/sections/sensors.css' in html,
            "Static JS": 'js/sections/_sensors_functions.js' in html,
            "Init JS": 'js/sections/sensors_init.js' in html,
        }
        
        all_passed = True
        for check_name, result in checks.items():
            if result:
                print_success(f"  ✓ {check_name}")
            else:
                print_error(f"  ✗ {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def run_all_tests():
    """Run all tests in sequence"""
    print_header("Sensor Data Module E2E Tests")
    
    results = {}
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print_error(f"Server not responding at {BASE_URL}")
        print_warning("Please start the Flask server first: python run.py")
        sys.exit(1)
    
    # Test entry exists
    if not test_entry_exists():
        print_error("Cannot continue without a test entry")
        sys.exit(1)
    
    # Run API tests
    results['sensor_types'] = test_sensor_types_endpoint()
    
    sensor_id = test_create_sensor_reading()
    results['create_reading'] = sensor_id is not None
    
    if sensor_id:
        results['get_data'] = test_get_sensor_data(sensor_id)
        results['update_reading'] = test_update_sensor_reading(sensor_id)
        results['time_range'] = test_time_range_filtering()
        results['delete_reading'] = test_delete_sensor_reading(sensor_id)
    else:
        print_warning("Skipping tests that require sensor_id")
        results['get_data'] = False
        results['update_reading'] = False
        results['time_range'] = False
        results['delete_reading'] = False
    
    # Test frontend
    results['frontend_page'] = test_frontend_page()
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✅ All tests passed!{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ Some tests failed{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(130)
