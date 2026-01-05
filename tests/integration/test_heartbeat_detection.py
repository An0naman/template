#!/usr/bin/env python3
"""
Test script for heartbeat detection functionality
"""

from datetime import datetime, timezone, timedelta
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.sensor_master_api import calculate_sensor_status


def test_calculate_sensor_status():
    """Test the sensor status calculation function"""
    print("Testing sensor status calculation...\n")
    
    # Test 1: No last_check_in (None)
    result = calculate_sensor_status(None)
    print(f"Test 1 - No check-in: {result}")
    assert result == 'pending', "Should return 'pending' when no check-in"
    
    # Test 2: Recent check-in (2 minutes ago) - should be online
    recent = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    result = calculate_sensor_status(recent, timeout_minutes=5)
    print(f"Test 2 - Recent check-in (2 min ago): {result}")
    assert result == 'online', "Should return 'online' for recent check-in"
    
    # Test 3: Old check-in (10 minutes ago) - should be offline
    old = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    result = calculate_sensor_status(old, timeout_minutes=5)
    print(f"Test 3 - Old check-in (10 min ago): {result}")
    assert result == 'offline', "Should return 'offline' for old check-in"
    
    # Test 4: Exactly at timeout boundary (5 minutes ago) - might be online or offline depending on milliseconds
    boundary = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    result = calculate_sensor_status(boundary, timeout_minutes=5)
    print(f"Test 4 - At boundary (5 min ago): {result}")
    # At the boundary, the result could be either online or offline depending on precision
    assert result in ['online', 'offline'], "Should return valid status at timeout boundary"
    
    # Test 5: Just past timeout (5.1 minutes ago)
    just_past = (datetime.now(timezone.utc) - timedelta(minutes=5, seconds=6)).isoformat()
    result = calculate_sensor_status(just_past, timeout_minutes=5)
    print(f"Test 5 - Just past boundary (5.1 min ago): {result}")
    assert result == 'offline', "Should return 'offline' just past timeout"
    
    # Test 6: Different datetime format (SQLite format)
    sqlite_format = (datetime.now(timezone.utc) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    result = calculate_sensor_status(sqlite_format, timeout_minutes=5)
    print(f"Test 6 - SQLite format (2 min ago): {result}")
    assert result == 'online', "Should handle SQLite datetime format"
    
    print("\n✅ All tests passed!")
    return True


def test_database_status_update():
    """Test updating sensor status in database"""
    print("\nTesting database status update...")
    
    try:
        import sqlite3
        
        # Connect directly to database file (avoid Flask context requirements)
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'template.db')
        
        if not os.path.exists(db_path):
            print(f"⚠️  Database not found at {db_path}")
            return True
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if we have any sensors
        cursor.execute('SELECT COUNT(*) as count FROM SensorRegistration')
        count = cursor.fetchone()['count']
        print(f"Found {count} registered sensors in database")
        
        if count > 0:
            # Get sensor details
            cursor.execute('''
                SELECT sensor_id, sensor_name, last_check_in, status 
                FROM SensorRegistration 
                LIMIT 5
            ''')
            sensors = cursor.fetchall()
            
            print("\nSensor Status Summary:")
            print("-" * 80)
            for sensor in sensors:
                calculated_status = calculate_sensor_status(sensor['last_check_in'])
                db_status = sensor['status']
                
                last_check_display = sensor['last_check_in'] if sensor['last_check_in'] else 'Never'
                
                status_match = "✓" if calculated_status == db_status else "✗"
                
                print(f"{status_match} {sensor['sensor_id'][:20]:20} | "
                      f"DB: {db_status:8} | Calc: {calculated_status:8} | "
                      f"Last Check: {last_check_display}")
            
            print("-" * 80)
        else:
            print("⚠️  No sensors registered yet. Register a sensor to test status updates.")
        
        conn.close()
        print("\n✅ Database check completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 80)
    print("Heartbeat Detection Test Suite")
    print("=" * 80)
    
    # Test the calculation logic
    test_calculate_sensor_status()
    
    # Test database integration
    test_database_status_update()
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)
