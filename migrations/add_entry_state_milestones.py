#!/usr/bin/env python3
"""
Migration: Add Entry State Milestones
Creates the EntryStateMilestone table for tracking intended/planned status changes
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
    # Import here to avoid Flask app creation
    import os
    db_path = os.environ.get('DATABASE_PATH', 'data/template.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    """Add EntryStateMilestone table"""
    print("\n" + "=" * 60)
    print("MIGRATION: Add Entry State Milestones")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='EntryStateMilestone'
        """)
        
        if cursor.fetchone():
            print("⚠️  EntryStateMilestone table already exists. Skipping creation.")
            return True
        
        print("Creating EntryStateMilestone table...")
        
        # Create the EntryStateMilestone table
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
        
        # Create indexes for better query performance
        print("Creating indexes...")
        
        cursor.execute("""
            CREATE INDEX idx_milestone_entry 
            ON EntryStateMilestone(entry_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_milestone_target_date 
            ON EntryStateMilestone(target_date)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_milestone_completed 
            ON EntryStateMilestone(is_completed)
        """)
        
        conn.commit()
        
        print("\n✓ EntryStateMilestone table created successfully!")
        print("\nTable structure:")
        print("  - id: Primary key")
        print("  - entry_id: Reference to Entry")
        print("  - target_state_id: Reference to EntryState (intended status)")
        print("  - target_date: When this status change is expected")
        print("  - notes: Optional notes about the milestone")
        print("  - is_completed: Flag for whether milestone was reached")
        print("  - completed_at: When the milestone was actually completed")
        print("  - created_at/updated_at: Timestamps")
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
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
    """Remove EntryStateMilestone table (for development/testing)"""
    print("\n" + "=" * 60)
    print("ROLLBACK: Remove Entry State Milestones")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop indexes first
        print("Dropping indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_entry")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_target_date")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_completed")
        
        # Drop table
        print("Dropping EntryStateMilestone table...")
        cursor.execute("DROP TABLE IF EXISTS EntryStateMilestone")
        
        conn.commit()
        
        print("\n✓ Rollback completed successfully!")
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
    
    parser = argparse.ArgumentParser(description='Entry State Milestones Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
