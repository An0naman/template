#!/usr/bin/env python3
"""
Migration: Add max_height column to EntryLayoutSection table
Date: 2025-10-28
Description: Adds the max_height column to support configurable maximum heights for sections
"""

import sqlite3
import os
import sys

def add_max_height_column():
    """Add max_height column to EntryLayoutSection table"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'homebrew.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        print(f"📊 Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(entry_layout_sections)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'max_height' in columns:
            print("✓ Column 'max_height' already exists")
            return True
        
        # Add max_height column
        print("Adding max_height column to entry_layout_sections table...")
        cursor.execute('''
            ALTER TABLE entry_layout_sections 
            ADD COLUMN max_height INTEGER
        ''')
        
        conn.commit()
        print("✓ Successfully added max_height column")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(entry_layout_sections)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'max_height' in columns:
            print("✓ Verified: max_height column exists")
            return True
        else:
            print("❌ Error: Column was not added")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add max_height column to EntryLayoutSection")
    print("=" * 60)
    
    success = add_max_height_column()
    
    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
