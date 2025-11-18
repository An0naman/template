#!/usr/bin/env python3
"""
Migration: Add status trigger fields to EntryState table

This migration adds two boolean fields to the EntryState table:
- sets_commenced: When true, setting this status will populate commenced_at if not already set
- sets_ended: When true, setting this status will populate actual_end_date with current timestamp

This allows configuring which statuses should automatically set these important date fields.

Usage:
    python migrations/add_status_triggers_to_entry_state.py         # Apply migration
    python migrations/add_status_triggers_to_entry_state.py --down  # Rollback migration
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
    """Add status trigger fields to EntryState table"""
    print("\n" + "=" * 60)
    print("MIGRATION: Add Status Triggers to EntryState")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='EntryState'
        """)
        
        if not cursor.fetchone():
            print("⚠️  EntryState table does not exist.")
            return False
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(EntryState)")
        columns = [row[1] for row in cursor.fetchall()]
        
        sets_commenced_exists = 'sets_commenced' in columns
        sets_ended_exists = 'sets_ended' in columns
        
        if sets_commenced_exists and sets_ended_exists:
            print("⚠️  Status trigger columns already exist. Skipping migration.")
            return True
        
        print("Adding status trigger columns to EntryState table...")
        
        # Add sets_commenced column
        if not sets_commenced_exists:
            print("- Adding sets_commenced column...")
            cursor.execute("""
                ALTER TABLE EntryState 
                ADD COLUMN sets_commenced INTEGER DEFAULT 0
            """)
            print("  ✓ sets_commenced column added")
        else:
            print("  ⊙ sets_commenced column already exists")
        
        # Add sets_ended column
        if not sets_ended_exists:
            print("- Adding sets_ended column...")
            cursor.execute("""
                ALTER TABLE EntryState 
                ADD COLUMN sets_ended INTEGER DEFAULT 0
            """)
            print("  ✓ sets_ended column added")
        else:
            print("  ⊙ sets_ended column already exists")
        
        # Create indexes for the new columns for better query performance
        print("\nCreating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entry_state_sets_commenced 
            ON EntryState(sets_commenced) WHERE sets_commenced = 1
        """)
        print("✓ Index on sets_commenced created")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entry_state_sets_ended 
            ON EntryState(sets_ended) WHERE sets_ended = 1
        """)
        print("✓ Index on sets_ended created")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nColumns Added:")
        print("- sets_commenced: INTEGER (0/1) - Triggers commenced_at when status is set")
        print("- sets_ended: INTEGER (0/1) - Triggers actual_end_date when status is set")
        print("\nNext steps:")
        print("1. Update entry_state_api.py to handle new fields")
        print("2. Update entry_api.py to check triggers on status change")
        print("3. Update state management UI to allow setting these flags")
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
    """Remove status trigger fields from EntryState table"""
    print("\n" + "=" * 60)
    print("ROLLBACK: Remove Status Triggers from EntryState")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(EntryState)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'sets_commenced' not in columns and 'sets_ended' not in columns:
            print("⚠️  Status trigger columns do not exist. Nothing to rollback.")
            return True
        
        print("⚠️  SQLite does not support dropping columns directly.")
        print("To rollback, you would need to:")
        print("1. Create a new EntryState table without the trigger columns")
        print("2. Copy all data except sets_commenced and sets_ended")
        print("3. Drop the old table")
        print("4. Rename the new table")
        print("\nThis is a destructive operation and should be done manually if needed.")
        print("For now, the columns will remain but can be ignored.")
        
        # Drop the indexes instead
        print("\nDropping indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_state_sets_commenced")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_state_sets_ended")
        conn.commit()
        print("✓ Indexes dropped")
        
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
