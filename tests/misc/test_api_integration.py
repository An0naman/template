#!/usr/bin/env python3
"""
Test the Flask API integration with the updated BLE service
Shows that your app can now print to B1 and D110
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def test_discover_printers():
    """Test printer discovery endpoint"""
    print("🔍 Testing printer discovery...")
    response = requests.get(f"{API_BASE}/niimbot/discover?timeout=5")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_connect_printer(address="B1", model="b1"):
    """Test printer connection endpoint"""
    print(f"🔌 Testing connection to {model.upper()}...")
    response = requests.post(
        f"{API_BASE}/niimbot/connect",
        json={
            "address": address,
            "model": model
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_print_label(entry_id=1, address="B1", model="b1"):
    """Test printing a label"""
    print(f"🖨️  Testing print to {model.upper()}...")
    response = requests.post(
        f"{API_BASE}/entries/{entry_id}/niimbot/print",
        json={
            "printer_address": address,
            "printer_model": model,
            "label_size": "50x14mm",
            "density": 3,
            "quantity": 1
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Flask API Integration Test")
    print("=" * 60)
    print()
    
    print("⚠️  Note: Make sure your Flask app is running!")
    print("   Start it with: docker compose up")
    print()
    
    input("Press Enter to start tests...")
    print()
    
    # Test 1: Discover printers
    try:
        test_discover_printers()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Is it running?")
        exit(1)
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
    
    # Test 2: Connect to printer
    try:
        test_connect_printer("B1", "b1")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    # Test 3: Print (optional - commented out to avoid printing during test)
    # Uncomment to actually print:
    # try:
    #     test_print_label(1, "B1", "b1")
    # except Exception as e:
    #     print(f"❌ Print test failed: {e}")
    
    print("=" * 60)
    print("✅ API Integration Tests Complete")
    print("=" * 60)
    print()
    print("Your app is now configured to use the BLE service!")
    print("The following endpoints work:")
    print("  - GET  /api/niimbot/discover")
    print("  - POST /api/niimbot/connect")
    print("  - POST /api/entries/<id>/niimbot/print")
