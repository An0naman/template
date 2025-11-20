#!/usr/bin/env python3
"""
Test script to verify sensor toggle functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import get_system_parameters

def test_sensor_parameter():
    """Test that the enable_sensors parameter exists and has a default value"""
    app = create_app()
    with app.app_context():
        params = get_system_parameters()
        
        print("=" * 60)
        print("Sensor Toggle Parameter Test")
        print("=" * 60)
        
        if 'enable_sensors' in params:
            print(f"✓ enable_sensors parameter exists")
            print(f"  Current value: {params['enable_sensors']}")
            print(f"  Type: {type(params['enable_sensors'])}")
            
            # Test the conditional logic
            is_enabled = params.get('enable_sensors', '1') == '1'
            print(f"  Sensors are: {'ENABLED' if is_enabled else 'DISABLED'}")
            
            return True
        else:
            print("✗ enable_sensors parameter NOT FOUND")
            print("  Available parameters:")
            for key in sorted(params.keys()):
                print(f"    - {key}")
            return False

def main():
    try:
        result = test_sensor_parameter()
        print("=" * 60)
        if result:
            print("✓ Test PASSED - Sensor toggle parameter configured correctly")
            print("\nTo test the feature:")
            print("1. Start the application: docker-compose up -d --build template")
            print("2. Navigate to the Settings page (Maintenance Module)")
            print("3. Look for the 'Sensor Functionality' toggle in System Configuration")
            print("4. Toggle it on/off and refresh to see sensor elements appear/disappear")
        else:
            print("✗ Test FAILED - Sensor toggle parameter missing")
        print("=" * 60)
        return 0 if result else 1
    except Exception as e:
        print(f"✗ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())
