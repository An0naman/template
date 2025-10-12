#!/usr/bin/env python3
"""
Migration: Add custom_sql_query column to SavedSearch table
"""

import sqlite3
import sys
import os

def run_migration(db_path):
    """Add custom_sql_query column to SavedSearch table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(SavedSearch)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'custom_sql_query' not in columns:
            print("Adding custom_sql_query column to SavedSearch table...")
            cursor.execute("""
                ALTER TABLE SavedSearch 
                ADD COLUMN custom_sql_query TEXT
            """)
            conn.commit()
            print("✓ Successfully added custom_sql_query column")
        else:
            print("✓ custom_sql_query column already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        return False

if __name__ == "__main__":
    # Default database path
    db_path = os.environ.get('DATABASE_PATH', '/app/data/template.db')
    
    # Allow override via command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"Running migration on database: {db_path}")
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
