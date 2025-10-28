#!/usr/bin/env python3
"""
Migration: Create Entry State Milestones with Ordering
Creates the EntryStateMilestone table with order_position and duration_days fields
for cumulative timeline calculation.
"""

import sqlite3
import sys
import os

# Add parent directory to path to import database utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template.db')
    return sqlite3.connect(db_path)

def migrate():
    """Create or update EntryStateMilestone table with ordering support"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("MIGRATION: Entry State Milestones with Ordering")
    print("=" * 60)
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='EntryStateMilestone'
        """)
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("\nTable exists. Checking schema...")
            cursor.execute("PRAGMA table_info(EntryStateMilestone)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            print(f"DEBUG: Found columns: {list(columns.keys())}")
            
            # Check if we need to migrate from old schema
            has_order = 'order_position' in columns
            has_duration = 'duration_days' in columns
            has_days_from_start = 'days_from_start' in columns
            
            print(f"DEBUG: has_order={has_order}, has_duration={has_duration}, has_days_from_start={has_days_from_start}")
            
            if has_order and has_duration:
                print("✓ Table already has correct schema. No migration needed.")
                return
            
            if has_days_from_start:
                print("\nMigrating from days_from_start to duration_days with ordering...")
                
                # Check if we have target_state_name column (newer schema)
                has_state_name = 'target_state_name' in columns
                
                if has_state_name:
                    # Backup existing data (newer schema with target_state_name)
                    cursor.execute("""
                        SELECT id, entry_id, target_state_id, target_state_name, target_state_color,
                               days_from_start, notes, is_completed, created_at, updated_at
                        FROM EntryStateMilestone
                        ORDER BY entry_id, days_from_start
                    """)
                else:
                    # Backup existing data (older schema without target_state_name)
                    # We'll fetch state info from EntryState table
                    cursor.execute("""
                        SELECT m.id, m.entry_id, m.target_state_id, es.name, es.color,
                               m.days_from_start, m.notes, m.is_completed, m.created_at, m.updated_at
                        FROM EntryStateMilestone m
                        JOIN EntryState es ON m.target_state_id = es.id
                        ORDER BY m.entry_id, m.days_from_start
                    """)
                
                milestones = cursor.fetchall()
                print(f"✓ Backed up {len(milestones)} milestones")
                
                # Drop existing table
                cursor.execute("DROP TABLE EntryStateMilestone")
                print("✓ Dropped old table")
        else:
            print("\nCreating new EntryStateMilestone table...")
            milestones = []
        
        # Create table with correct schema
        cursor.execute("""
            CREATE TABLE EntryStateMilestone (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                target_state_id INTEGER NOT NULL,
                target_state_name TEXT NOT NULL,
                target_state_color TEXT,
                order_position INTEGER NOT NULL DEFAULT 1,
                duration_days INTEGER NOT NULL CHECK(duration_days > 0),
                notes TEXT,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (target_state_id) REFERENCES EntryState(id) ON DELETE CASCADE
            )
        """)
        print("✓ Created table with order_position and duration_days")
        
        # Restore data if we had any
        if milestones:
            print(f"\nRestoring {len(milestones)} milestones with sequential ordering...")
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
            
            print(f"✓ Restored milestones with ordering")
        
        # Create indexes
        print("\nCreating indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_entry")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_order")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_completed")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_target_date")
        cursor.execute("DROP INDEX IF EXISTS idx_milestone_days")
        
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
        print("\nTable structure:")
        for col in new_columns:
            print(f"  - {col[1]}: {col[2]}")
        
        print("\nKey features:")
        print("  ✓ order_position: Sequential ordering of milestones (1, 2, 3, ...)")
        print("  ✓ duration_days: How long this status lasts (> 0)")
        print("  ✓ Cumulative logic: Position = sum of all previous durations")
        print("  ✓ Example: Order 1 (2 days), Order 2 (3 days), Order 3 (5 days)")
        print("           = Day 2, Day 5, Day 10 from creation")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
