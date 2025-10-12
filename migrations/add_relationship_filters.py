#!/usr/bin/env python3
"""
Migration: Add relationship filtering to SavedSearch table
This allows users to filter entries based on their relationships with other entries.
"""

import sqlite3
import sys

def run_migration(db_path):
    """Add relationship filter columns to SavedSearch table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(SavedSearch)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'relationship_filters' not in columns:
            print("Adding relationship_filters column to SavedSearch...")
            cursor.execute("""
                ALTER TABLE SavedSearch 
                ADD COLUMN relationship_filters TEXT DEFAULT NULL
            """)
            print("✓ Added relationship_filters column")
        else:
            print("⚠ relationship_filters column already exists")
        
        if 'relationship_logic' not in columns:
            print("Adding relationship_logic column to SavedSearch...")
            cursor.execute("""
                ALTER TABLE SavedSearch 
                ADD COLUMN relationship_logic TEXT DEFAULT 'AND'
            """)
            print("✓ Added relationship_logic column")
        else:
            print("⚠ relationship_logic column already exists")
        
        conn.commit()
        print("✓ Migration completed successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_relationship_filters.py <database_path>")
        print("Example: python3 add_relationship_filters.py /app/data/template.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
