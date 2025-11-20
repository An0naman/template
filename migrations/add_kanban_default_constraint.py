#!/usr/bin/env python3
"""
Migration: Add unique constraint for default Kanban boards per entry type
"""

import sqlite3
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def migrate():
    """Add unique constraint to ensure only one default board per entry type"""
    
    # Determine database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Ensuring only one default board per entry type...")
        
        # First, clean up any duplicate defaults
        cursor.execute("""
            WITH RankedDefaults AS (
                SELECT id, entry_type_id,
                       ROW_NUMBER() OVER (PARTITION BY entry_type_id ORDER BY created_at DESC) as rn
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
            print(f"✓ Cleaned up {rows_updated} duplicate default board(s)")
        else:
            print("✓ No duplicate defaults found")
        
        # Create a unique partial index to enforce the constraint
        print("Creating unique constraint index...")
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_kanban_board_default_per_type
            ON KanbanBoard(entry_type_id)
            WHERE is_default = 1
        """)
        print("✓ Unique constraint index created")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        print("\nThis ensures only one default board per entry type at the database level.")
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
