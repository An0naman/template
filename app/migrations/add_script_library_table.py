#!/usr/bin/env python3
"""
Migration: Add ScriptLibrary Table
===================================

This migration adds the ScriptLibrary table to store reusable scripts
that can be assigned to multiple sensors.

Tables:
-------
- ScriptLibrary: Stores reusable scripts

Usage:
------
python app/migrations/add_script_library_table.py
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
            WHERE type='table' AND name='ScriptLibrary'
        """)
        
        if cursor.fetchone():
            print("✓ ScriptLibrary table already exists, skipping creation")
        else:
            print("Creating ScriptLibrary table...")
            cursor.execute("""
                CREATE TABLE ScriptLibrary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    script_content TEXT NOT NULL,
                    script_version TEXT DEFAULT '1.0.0',
                    script_type TEXT DEFAULT 'arduino',
                    description TEXT,
                    target_sensor_type TEXT, -- Optional: suggest which sensor type this is for
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ ScriptLibrary table created")
            
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
