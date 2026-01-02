#!/usr/bin/env python3
"""
Test script for Sensor Master Control API
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from app.api import sensor_master_api
        print("✓ sensor_master_api imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sensor_master_api: {e}")
        return False
    
    try:
        from app.services import sensor_master_service
        print("✓ sensor_master_service imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sensor_master_service: {e}")
        return False
    
    return True

def test_database_tables():
    """Test that database tables exist"""
    print("\nTesting database tables...")
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'template.db')
        
        if not os.path.exists(db_path):
            print(f"✗ Database not found at {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = [
            'SensorRegistration',
            'SensorCommandQueue'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"✓ Table {table} exists")
            else:
                print(f"✗ Table {table} not found")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_files_exist():
    """Test that all required files exist"""
    print("\nTesting file existence...")
    
    files = [
        'app/api/sensor_master_api.py',
        'app/services/sensor_master_service.py',
        'app/templates/sensor_master_control.html',
        'app/migrations/add_sensor_master_control.py',
        'scripts/esp32_master_control_integration.py'
    ]
    
    optional_files = [
        'docs/SENSOR_MASTER_CONTROL.md'
    ]
    
    all_exist = True
    for filepath in files:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✓ {filepath} ({size:,} bytes)")
        else:
            print(f"✗ {filepath} not found")
            all_exist = False
            
    for filepath in optional_files:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✓ {filepath} ({size:,} bytes)")
        else:
            print(f"⚠️ {filepath} not found (optional/docs)")
    
    return all_exist

def main():
    """Run all tests"""
    print("=" * 60)
    print("Sensor Master Control - System Test")
    print("=" * 60)
    
    results = []
    
    # Test file existence
    results.append(("File existence", test_files_exist()))
    
    # Test database
    results.append(("Database tables", test_database_tables()))
    
    # Test imports (may fail without Flask installed, but files are there)
    results.append(("Module imports", test_imports()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check output above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
