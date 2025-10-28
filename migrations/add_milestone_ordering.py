#!/usr/bin/env python3
"""
Migration: Add Milestone Ordering and Duration
Adds order_position field and renames days_from_start to duration_days
to support cumulative timeline calculation.
"""

import sqlite3
import sys
import os

# Add parent directory to path to import database utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'homebrew.db')
    return sqlite3.connect(db_path)

def migrate():
    """Add ordering and rename duration field"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("MIGRATION: Add Milestone Ordering and Duration")
    print("=" * 60)
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(EntryStateMilestone)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        print("\nCurrent columns:", list(columns.keys()))
        
        # Backup existing data
        print("\nBacking up existing milestones...")
        cursor.execute("""
            SELECT id, entry_id, target_state_id, target_state_name, target_state_color,
                   days_from_start, notes, is_completed, created_at, updated_at
            FROM EntryStateMilestone
            ORDER BY entry_id, days_from_start
        """)
        milestones = cursor.fetchall()
        print(f"✓ Backed up {len(milestones)} milestones")
        
        # Drop existing table
        print("\nDropping old table structure...")
        cursor.execute("DROP TABLE IF EXISTS EntryStateMilestone")
        
        # Create new table with order_position and duration_days
        print("Creating new table structure...")
        cursor.execute("""
            CREATE TABLE EntryStateMilestone (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                target_state_id INTEGER NOT NULL,
                target_state_name TEXT NOT NULL,
                target_state_color TEXT,
                order_position INTEGER NOT NULL DEFAULT 0,
                duration_days INTEGER NOT NULL CHECK(duration_days >= 0),
                notes TEXT,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (target_state_id) REFERENCES EntryState(id) ON DELETE CASCADE
            )
        """)
        print("✓ New table structure created")
        
        # Restore data with sequential ordering per entry
        print("\nRestoring milestones with sequential ordering...")
        current_entry_id = None
        order_position = 0
        
        for milestone in milestones:
            mid, entry_id, state_id, state_name, state_color, days_from_start, notes, is_completed, created_at, updated_at = milestone
            
            # Reset order position for new entry
            if entry_id != current_entry_id:
                current_entry_id = entry_id
                order_position = 1
            else:
                order_position += 1
            
            cursor.execute("""
                INSERT INTO EntryStateMilestone 
                (entry_id, target_state_id, target_state_name, target_state_color,
                 order_position, duration_days, notes, is_completed, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, state_id, state_name, state_color, 
                  order_position, days_from_start, notes, is_completed, created_at, updated_at))
        
        print(f"✓ Restored {len(milestones)} milestones with ordering")
        
        # Create indexes
        print("\nCreating indexes...")
        cursor.execute("CREATE INDEX idx_milestone_entry ON EntryStateMilestone(entry_id)")
        cursor.execute("CREATE INDEX idx_milestone_order ON EntryStateMilestone(entry_id, order_position)")
        cursor.execute("CREATE INDEX idx_milestone_completed ON EntryStateMilestone(is_completed)")
        print("✓ Indexes created")
        
        # Commit changes
        conn.commit()
        
        # Verify new structure
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
        cursor.execute("PRAGMA table_info(EntryStateMilestone)")
        new_columns = cursor.fetchall()
        print("\nUpdated table structure:")
        for col in new_columns:
            print(f"  - {col[1]}: {col[2]}")
        
        print("\nKey changes:")
        print("  ✓ Added: order_position (INTEGER, sequential ordering)")
        print("  ✓ Renamed: days_from_start → duration_days")
        print("  ✓ Logic: Each milestone defines duration, position = sum of previous durations")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
