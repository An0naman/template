#!/usr/bin/env python3
"""
Database initialization script for the template application.
Run this to set up the database schema and create necessary tables.
"""

import os
import sys

# Add the current directory to Python path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import init_db

def main():
    print("Initializing database...")
    try:
        # Create Flask app and context
        app = create_app()
        with app.app_context():
            init_db()
        
        print("✅ Database initialized successfully!")
        print("\nThe following tables have been created:")
        print("- EntryType (for different types of entries)")
        print("- Entry (main entries/batches)")
        print("- SensorData (sensor readings)")
        print("- RegisteredDevices (ESP32 devices)")
        print("- DeviceEntryLinks (many-to-many links between devices and entries)")
        print("- SystemParameters (configuration settings)")
        print("- NotificationRules (alert configurations)")
        print("- And more...")
        print("\nYou can now run the application!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
