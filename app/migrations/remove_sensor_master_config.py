#!/usr/bin/env python3
"""
Migration: Remove SensorMasterConfig Table
==========================================

This migration removes the SensorMasterConfig table as requested by the user.
Configuration templates are being replaced by direct script assignments.

Usage:
------
python app/migrations/remove_sensor_master_config.py
"""

import sqlite3
import sys
import os

# Add parent directory to path to import db module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def run_migration(db_path):
    """Run the migration"""
    print(f"Running migration on {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SensorMasterConfig'
        """)
        
        if not cursor.fetchone():
            print("✓ SensorMasterConfig table does not exist, skipping removal")
        else:
            print("Removing SensorMasterConfig table...")
            cursor.execute("DROP TABLE SensorMasterConfig")
            print("✓ SensorMasterConfig table removed")
            
        conn.commit()
        conn.close()
        print("Migration completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

if __name__ == "__main__":
    # Determine database path
    db_path = os.environ.get('DATABASE_PATH')
    
    if not db_path:
        # Default path relative to this script
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        db_path = os.path.join(base_dir, 'instance', 'template.db')
        
        # If instance/template.db doesn't exist, try data/template.db (older structure)
        if not os.path.exists(db_path):
             db_path = os.path.join(base_dir, 'data', 'template.db')
        
    if not os.path.exists(os.path.dirname(db_path)):
        print(f"Error: Database directory does not exist: {os.path.dirname(db_path)}")
        sys.exit(1)
        
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
