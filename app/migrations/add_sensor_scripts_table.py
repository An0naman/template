#!/usr/bin/env python3
"""
Migration: Add SensorScripts Table
===================================

This migration adds the SensorScripts table to store dynamic scripts/instructions
that can be sent to sensors over WiFi.

Tables:
-------
- SensorScripts: Stores executable scripts for sensors

Usage:
------
python app/migrations/add_sensor_scripts_table.py

Or set DATABASE_PATH environment variable:
DATABASE_PATH=./data/template.db python app/migrations/add_sensor_scripts_table.py
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add parent directory to path to import db module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def run_migration(db_path):
    """Run the migration"""
    print(f"Running migration on database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SensorScripts'
        """)
        
        if cursor.fetchone():
            print("✓ SensorScripts table already exists, skipping creation")
        else:
            print("Creating SensorScripts table...")
            cursor.execute("""
                CREATE TABLE SensorScripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    script_content TEXT NOT NULL,
                    script_version TEXT DEFAULT '1.0.0',
                    script_type TEXT DEFAULT 'arduino',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
                )
            """)
            print("✓ SensorScripts table created")
        
        # Create indexes
        print("Creating indexes...")
        
        # Index on sensor_id for quick lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_scripts_sensor_id 
            ON SensorScripts(sensor_id)
        """)
        
        # Index on is_active for filtering active scripts
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_scripts_active 
            ON SensorScripts(is_active)
        """)
        
        # Composite index for quick active script lookup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_scripts_sensor_active 
            ON SensorScripts(sensor_id, is_active)
        """)
        
        print("✓ Indexes created")
        
        # Create trigger to update updated_at timestamp
        print("Creating trigger...")
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_sensor_scripts_timestamp 
            AFTER UPDATE ON SensorScripts
            BEGIN
                UPDATE SensorScripts 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        print("✓ Trigger created")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    # Get database path from environment or use default
    db_path = os.environ.get('DATABASE_PATH', './data/template.db')
    
    if not os.path.exists(os.path.dirname(db_path)):
        print(f"Error: Directory does not exist: {os.path.dirname(db_path)}")
        sys.exit(1)
    
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
