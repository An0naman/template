#!/usr/bin/env python3
"""
Migration: Update Kanban default constraint to allow only one default across all boards
"""

import sqlite3
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def migrate():
    """Update constraint to ensure only one default board total"""
    
    # Determine database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Ensuring only one default board total...")
        
        # First, clean up so only one default exists
        cursor.execute("""
            WITH RankedDefaults AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
                FROM KanbanBoard
                WHERE is_default = 1
            )
            UPDATE KanbanBoard
            SET is_default = 0
            WHERE id IN (
                SELECT id FROM RankedDefaults WHERE rn > 1
            )
        """)
        
        rows_updated = cursor.rowcount
        if rows_updated > 0:
            print(f"✓ Cleaned up {rows_updated} extra default board(s)")
        else:
            print("✓ No extra defaults found")
        
        # Drop old per-entry-type constraint if it exists
        print("Removing old per-entry-type constraint...")
        cursor.execute("DROP INDEX IF EXISTS idx_kanban_board_default_per_type")
        print("✓ Old constraint removed")
        
        # Create a unique partial index to enforce single default across all boards
        print("Creating new single-default constraint...")
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_kanban_board_single_default
            ON KanbanBoard(is_default)
            WHERE is_default = 1
        """)
        print("✓ New constraint created")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        print("\nThis ensures only ONE default board exists across all entry types.")
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
