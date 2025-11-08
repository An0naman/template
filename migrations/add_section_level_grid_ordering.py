"""
Migration: Add Section-Level Grid Ordering Support

This migration adds section_id to RelationshipGridOrder table to support
per-section ordering instead of per-entry-type ordering.

Date: 2025-11-08
"""

import sqlite3
import sys
import os

def run_migration(db_path='data/template.db'):
    """Add section_id to RelationshipGridOrder table"""
    
    print(f"Running migration: Add section-level grid ordering support")
    print(f"Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if RelationshipGridOrder table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='RelationshipGridOrder'
        """)
        
        if not cursor.fetchone():
            print("  ⚠ RelationshipGridOrder table does not exist - skipping migration")
            return
        
        # Check if section_id column already exists
        cursor.execute("PRAGMA table_info(RelationshipGridOrder)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'section_id' in columns:
            print("  ✓ section_id column already exists - skipping migration")
            return
        
        print("  → Adding section_id column to RelationshipGridOrder...")
        
        # Create new table with section_id
        cursor.execute("""
            CREATE TABLE RelationshipGridOrder_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type_id INTEGER NOT NULL,
                section_id INTEGER,
                relationship_definition_id INTEGER NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
                FOREIGN KEY (section_id) REFERENCES EntryLayoutSection(id) ON DELETE CASCADE,
                FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
                UNIQUE(entry_type_id, section_id, relationship_definition_id)
            )
        """)
        
        # Copy data from old table (section_id will be NULL for old entries)
        cursor.execute("""
            INSERT INTO RelationshipGridOrder_new 
                (id, entry_type_id, relationship_definition_id, display_order, created_at, updated_at)
            SELECT 
                id, entry_type_id, relationship_definition_id, display_order, created_at, updated_at
            FROM RelationshipGridOrder
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE RelationshipGridOrder")
        
        # Rename new table
        cursor.execute("ALTER TABLE RelationshipGridOrder_new RENAME TO RelationshipGridOrder")
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationship_grid_order_entry_type 
            ON RelationshipGridOrder(entry_type_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationship_grid_order_section 
            ON RelationshipGridOrder(section_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationship_grid_order_display 
            ON RelationshipGridOrder(entry_type_id, section_id, display_order)
        """)
        
        conn.commit()
        print("  ✓ Successfully added section_id column to RelationshipGridOrder")
        print("  ✓ Created indexes for better query performance")
        print("  ℹ Existing grid orders will apply to all sections (section_id = NULL)")
        print("  ℹ New section-specific orders will override entry-type level orders")
        
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/template.db'
    run_migration(db_path)
