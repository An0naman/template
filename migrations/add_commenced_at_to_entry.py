#!/usr/bin/env python3
"""
Migration: Add commenced_at field to Entry table

This migration adds a commenced_at field to track when an entry actually started,
separate from when it was created. This is particularly useful for milestone
calculations where the start date should be when work commenced, not when the
entry was initially created in the system.

Usage:
    python migrations/add_commenced_at_to_entry.py         # Apply migration
    python migrations/add_commenced_at_to_entry.py --down  # Rollback migration
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set Flask environment
os.environ['FLASK_APP'] = 'run.py'


def get_db_connection():
    """Get direct database connection without Flask context"""
    db_path = os.environ.get('DATABASE_PATH', 'data/template.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    """Add commenced_at column to Entry table"""
    print("\n" + "=" * 60)
    print("MIGRATION: Add commenced_at to Entry table")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='Entry'
        """)
        
        if not cursor.fetchone():
            print("⚠️  Entry table does not exist.")
            return False
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(Entry)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'commenced_at' in columns:
            print("⚠️  commenced_at column already exists. Skipping migration.")
            return True
        
        print("Adding commenced_at column to Entry table...")
        
        # Add the new column (NULL by default, will be populated with created_at for existing entries)
        cursor.execute("""
            ALTER TABLE Entry 
            ADD COLUMN commenced_at TEXT
        """)
        
        print("✓ Column added successfully")
        
        # For existing entries, set commenced_at = created_at as a reasonable default
        cursor.execute("""
            UPDATE Entry 
            SET commenced_at = created_at 
            WHERE commenced_at IS NULL
        """)
        
        rows_updated = cursor.rowcount
        print(f"✓ Updated {rows_updated} existing entries with commenced_at = created_at")
        
        # Create an index on commenced_at for better query performance
        print("Creating index on commenced_at...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entry_commenced_at 
            ON Entry(commenced_at)
        """)
        print("✓ Index created")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update milestone_api.py to use commenced_at")
        print("2. Update entry creation/update APIs to handle commenced_at")
        print("3. Update frontend to display and edit commenced_at")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


def rollback():
    """Remove commenced_at column from Entry table"""
    print("\n" + "=" * 60)
    print("ROLLBACK: Remove commenced_at from Entry table")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(Entry)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'commenced_at' not in columns:
            print("⚠️  commenced_at column does not exist. Nothing to rollback.")
            return True
        
        print("⚠️  SQLite does not support dropping columns directly.")
        print("To rollback, you would need to:")
        print("1. Create a new Entry table without commenced_at")
        print("2. Copy all data except commenced_at")
        print("3. Drop the old table")
        print("4. Rename the new table")
        print("\nThis is a destructive operation and should be done manually if needed.")
        print("For now, the column will remain but can be ignored.")
        
        # Drop the index instead
        print("\nDropping commenced_at index...")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_commenced_at")
        conn.commit()
        print("✓ Index dropped")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during rollback: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    if '--down' in sys.argv:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
