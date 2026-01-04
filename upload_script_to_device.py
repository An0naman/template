#!/usr/bin/env python3
"""
Upload a JSON script directly to an ESP32 device via the app's API
"""
import json
import requests
import sys
import argparse

def upload_script_to_device(json_file, device_id, app_url="http://localhost:5000"):
    """Upload a JSON script file to a specific device"""
    
    # Read the JSON script
    try:
        with open(json_file, 'r') as f:
            script_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file}' not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{json_file}': {e}")
        return False
    
    print(f"📄 Loaded script: {script_data.get('name', 'Unnamed')}")
    print(f"   Version: {script_data.get('version', 'N/A')}")
    print(f"   Description: {script_data.get('description', 'N/A')}")
    print(f"   Actions: {len(script_data.get('actions', []))}")
    
    # First, save to library
    library_payload = {
        "name": script_data.get("name", "Unnamed Script"),
        "script_content": json.dumps(script_data),
        "script_version": script_data.get("version", "1.0.0"),
        "script_type": "logic_builder",
        "description": script_data.get("description", ""),
        "target_sensor_type": script_data.get("target_sensor_type", "generic")
    }
    
    try:
        print(f"\n📤 Uploading to library at {app_url}...")
        response = requests.post(
            f"{app_url}/api/sensor-master/library-script",
            json=library_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            script_id = data.get('script_id')
            print(f"✅ Script saved to library (ID: {script_id})")
        else:
            print(f"⚠️ Library upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            # Continue anyway, might already exist
            script_id = None
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not connect to app: {e}")
        script_id = None
    
    # Now send directly to device
    device_payload = {
        "sensor_id": device_id,
        "script_content": json.dumps(script_data)
    }
    
    try:
        print(f"\n📡 Sending script to device {device_id}...")
        response = requests.post(
            f"{app_url}/api/sensor-master/deploy-script",
            json=device_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Script deployed to device successfully!")
            return True
        else:
            print(f"❌ Device upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to device: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload JSON script to ESP32 device")
    parser.add_argument("json_file", help="Path to the JSON script file")
    parser.add_argument("device_id", help="Device/Sensor ID")
    parser.add_argument("--url", default="http://localhost:5000", 
                       help="App URL (default: http://localhost:5000)")
    
    args = parser.parse_args()
    
    success = upload_script_to_device(args.json_file, args.device_id, args.url)
    sys.exit(0 if success else 1)
