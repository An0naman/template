#!/usr/bin/env python3
"""
Standalone database initialization script for the template framework.
This script creates the necessary device management tables.
"""

import sqlite3
import os

def get_database_path():
    """Get the database path based on the config"""
    # This mirrors the config.py logic
    current_dir = os.path.dirname(os.path.abspath(__file__))
    database_name = 'template.db'
    return os.path.join(current_dir, database_name)

def init_device_tables(conn):
    """Initialize device management tables"""
    cursor = conn.cursor()
    
    # Create RegisteredDevices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RegisteredDevices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            ip TEXT NOT NULL,
            device_type TEXT NOT NULL,
            capabilities TEXT,
            status TEXT DEFAULT 'unknown',
            last_seen TIMESTAMP,
            polling_enabled BOOLEAN DEFAULT 1,
            polling_interval INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create DeviceEntryLinks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeviceEntryLinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            entry_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES RegisteredDevices (id) ON DELETE CASCADE,
            FOREIGN KEY (entry_id) REFERENCES Entry (id) ON DELETE CASCADE,
            UNIQUE(device_id, entry_id)
        )
    ''')
    
    # Create DeviceSensorMapping table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeviceSensorMapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            sensor_name TEXT NOT NULL,
            entry_field TEXT NOT NULL,
            data_type TEXT DEFAULT 'text',
            unit TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES RegisteredDevices (id) ON DELETE CASCADE,
            UNIQUE(device_id, sensor_name)
        )
    ''')
    
    conn.commit()
    print("Device management tables created successfully!")

def main():
    """Main initialization function"""
    db_path = get_database_path()
    print(f"Initializing database at: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Warning: Database file {db_path} does not exist!")
        print("Creating new database file...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Initialize device tables
        init_device_tables(conn)
        
        # Check existing tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\nAvailable tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check device tables specifically
        device_tables = ['RegisteredDevices', 'DeviceEntryLinks', 'DeviceSensorMapping']
        print(f"\nDevice tables status:")
        for table_name in device_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return 1
    finally:
        conn.close()
    
    print(f"\nDatabase initialization complete!")
    return 0

if __name__ == '__main__':
    exit(main())
