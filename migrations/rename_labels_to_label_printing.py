#!/usr/bin/env python3
"""
Migration: Rename 'labels' section to 'label_printing'

This migration updates existing EntryLayoutSection records that use the old
'labels' section_type to use the new 'label_printing' section_type.
"""

import sqlite3
import sys
import os

def migrate(db_path='data/template.db'):
    """Migrate labels section to label_printing section"""
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("MIGRATION: Rename 'labels' section to 'label_printing'")
        print("=" * 70)
        print()
        
        # Check if there are any 'labels' sections
        cursor.execute("""
            SELECT COUNT(*) FROM EntryLayoutSection 
            WHERE section_type = 'labels'
        """)
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("✓ No 'labels' sections found - nothing to migrate")
            print()
            return True
        
        print(f"Found {count} 'labels' section(s) to migrate...")
        print()
        
        # Update all 'labels' sections to 'label_printing'
        cursor.execute("""
            UPDATE EntryLayoutSection 
            SET section_type = 'label_printing'
            WHERE section_type = 'labels'
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✓ Successfully updated {updated_count} section(s)")
        print()
        print("=" * 70)
        print("✓ Migration completed successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    # Support custom database path
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/template.db'
    success = migrate(db_path)
    sys.exit(0 if success else 1)
