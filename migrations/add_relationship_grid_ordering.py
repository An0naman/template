#!/usr/bin/env python3
"""
Migration: Add Relationship Grid Ordering Support

This migration adds the ability for users to customize the display order
of relationship type cards within the relationships section.

Tables Created:
- RelationshipGridOrder: Stores user preferences for grid ordering per entry
"""

import sqlite3
import sys
import os

def run_migration(db_path='data/template.db'):
    """Add relationship grid ordering support"""
    
    print("=" * 80)
    print("MIGRATION: Add Relationship Grid Ordering Support")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # ================================================================
        # Create RelationshipGridOrder table
        # ================================================================
        print("Creating RelationshipGridOrder table...")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='RelationshipGridOrder'
        """)
        
        if cursor.fetchone():
            print("  - RelationshipGridOrder table already exists")
        else:
            print("  - Creating RelationshipGridOrder table...")
            cursor.execute("""
                CREATE TABLE RelationshipGridOrder (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_type_id INTEGER NOT NULL,
                    relationship_definition_id INTEGER NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
                    FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
                    UNIQUE(entry_type_id, relationship_definition_id)
                )
            """)
            print("    ✓ Created RelationshipGridOrder table")
            print("    This table stores grid ordering preferences per entry type")
        
        # ================================================================
        # Create index for performance
        # ================================================================
        print("\nCreating indexes...")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_grid_order_entry_type
                ON RelationshipGridOrder(entry_type_id)
            """)
            print("  ✓ Created index on entry_type_id")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_grid_order_display
                ON RelationshipGridOrder(entry_type_id, display_order)
            """)
            print("  ✓ Created index on entry_type_id and display_order")
        except Exception as e:
            print(f"  ⚠ Error creating indexes: {e}")
        
        conn.commit()
        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        return True
        
    except Exception as e:
        conn.rollback()
        print("\n" + "=" * 80)
        print(f"❌ MIGRATION FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    # Support custom database path from command line
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/template.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        sys.exit(1)
    
    # Run migration
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
