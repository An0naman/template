#!/usr/bin/env python3
"""
Migration: Update Entry State Milestones to use days instead of dates
Changes target_date to days_from_start for better reusability
"""

import sqlite3
import sys
import os
from pathlib import Path

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
    """Update EntryStateMilestone to use days_from_start"""
    print("\n" + "=" * 60)
    print("MIGRATION: Update Milestones to Days-Based System")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='EntryStateMilestone'
        """)
        
        if not cursor.fetchone():
            print("⚠️  EntryStateMilestone table does not exist. Run add_entry_state_milestones.py first.")
            return False
        
        print("Updating EntryStateMilestone table structure...")
        
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        # First, check if we have any existing data
        cursor.execute("SELECT COUNT(*) FROM EntryStateMilestone")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing milestones. Backing up data...")
        
        # Clean up any previous backup
        cursor.execute("DROP TABLE IF EXISTS EntryStateMilestone_backup")
        
        # Rename existing table
        cursor.execute("ALTER TABLE EntryStateMilestone RENAME TO EntryStateMilestone_backup")
        
        # Drop old indexes (they're attached to the old table)
        print("Dropping old indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_entry")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_target_date")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_days")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_completed")
        
        # Create new table with days_from_start
        cursor.execute("""
            CREATE TABLE EntryStateMilestone (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                target_state_id INTEGER NOT NULL,
                days_from_start INTEGER NOT NULL,
                notes TEXT,
                is_completed INTEGER DEFAULT 0,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (target_state_id) REFERENCES EntryState(id) ON DELETE CASCADE,
                CHECK(days_from_start >= 0)
            )
        """)
        
        print("✓ New table structure created")
        
        # Migrate existing data if any
        if existing_count > 0:
            print(f"Migrating {existing_count} existing milestones...")
            print("⚠️  Note: target_date values will be lost. Manual recreation recommended.")
            cursor.execute("""
                INSERT INTO EntryStateMilestone 
                (id, entry_id, target_state_id, days_from_start, notes, is_completed, completed_at, created_at, updated_at)
                SELECT 
                    id, entry_id, target_state_id, 
                    7 as days_from_start,  -- Default to 7 days, needs manual update
                    notes, is_completed, completed_at, created_at, updated_at
                FROM EntryStateMilestone_backup
            """)
            print("✓ Data migrated (with default days_from_start=7)")
            print("⚠️  Please review and update milestone days manually")
            
            # Drop backup table
            cursor.execute("DROP TABLE EntryStateMilestone_backup")
        
        # Recreate indexes
        print("Creating indexes...")
        
        cursor.execute("""
            CREATE INDEX idx_milestone_entry 
            ON EntryStateMilestone(entry_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_milestone_days 
            ON EntryStateMilestone(days_from_start)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_milestone_completed 
            ON EntryStateMilestone(is_completed)
        """)
        
        conn.commit()
        
        print("\n✓ Migration completed successfully!")
        print("\nUpdated table structure:")
        print("  - id: Primary key")
        print("  - entry_id: Reference to Entry")
        print("  - target_state_id: Reference to EntryState")
        print("  - days_from_start: Days from entry creation (INTEGER)")
        print("  - notes: Optional notes")
        print("  - is_completed: Completion flag")
        print("  - completed_at: Completion timestamp")
        print("  - created_at/updated_at: Timestamps")
        
        print("\n" + "=" * 60)
        print("✓ Table now uses days-based milestone system!")
        print("=" * 60)
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def rollback():
    """Revert to date-based system (for development/testing)"""
    print("\n" + "=" * 60)
    print("ROLLBACK: Revert to Date-Based Milestones")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("⚠️  This will recreate the table with target_date field")
        print("⚠️  All existing milestone data will be lost!")
        
        # Drop current table
        cursor.execute("DROP TABLE IF EXISTS EntryStateMilestone")
        
        # Recreate with original structure
        cursor.execute("""
            CREATE TABLE EntryStateMilestone (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                target_state_id INTEGER NOT NULL,
                target_date TEXT NOT NULL,
                notes TEXT,
                is_completed INTEGER DEFAULT 0,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (target_state_id) REFERENCES EntryState(id) ON DELETE CASCADE
            )
        """)
        
        # Recreate indexes
        cursor.execute("CREATE INDEX idx_milestone_entry ON EntryStateMilestone(entry_id)")
        cursor.execute("CREATE INDEX idx_milestone_target_date ON EntryStateMilestone(target_date)")
        cursor.execute("CREATE INDEX idx_milestone_completed ON EntryStateMilestone(is_completed)")
        
        conn.commit()
        
        print("\n✓ Rollback completed - table reverted to date-based system")
        print("=" * 60)
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Error during rollback: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Milestones to Days-Based System')
    parser.add_argument('--rollback', action='store_true', help='Rollback to date-based system')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
