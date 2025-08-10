#!/usr/bin/env python3
"""
Migration: Add UserPreferences table for persistent filter settings
Created: 2024
"""

import sqlite3
import sys
import os

def migrate(db_path):
    """Add UserPreferences table to store persistent filter settings"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if UserPreferences table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='UserPreferences'
        """)
        
        if cursor.fetchone():
            print("UserPreferences table already exists, skipping migration")
            return True
        
        # Create UserPreferences table
        cursor.execute('''
            CREATE TABLE UserPreferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_name TEXT NOT NULL,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(preference_name)
            );
        ''')
        
        # Insert default filter preferences
        default_preferences = [
            ('default_view_type', 'all'),
            ('default_entry_type_filter', ''),
            ('default_status_filter', 'all'),
            ('default_result_limit', '50')
        ]
        
        cursor.executemany('''
            INSERT INTO UserPreferences (preference_name, preference_value)
            VALUES (?, ?)
        ''', default_preferences)
        
        conn.commit()
        print("Successfully created UserPreferences table")
        return True
        
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_user_preferences_table.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        sys.exit(1)
    
    success = migrate(db_path)
    sys.exit(0 if success else 1)
