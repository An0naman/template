#!/usr/bin/env python3
"""
Migration: Add Entry-Level Template Sharing

This migration adds target_entry_id to TemplateRelationshipSharing to support
granular entry-level template sharing instead of just relationship-type-level.

Before: Template shared with all entries of a relationship type
After: Template shared with specific selected entries

Changes:
- Add target_entry_id column to TemplateRelationshipSharing (nullable for backward compat)
- Remove UNIQUE constraint and replace with new one including target_entry_id
"""

import sqlite3
import sys
import os
from pathlib import Path

def get_db():
    """Get database connection"""
    db_path = os.environ.get('DATABASE_PATH', '/app/data/database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def migrate():
    """Run the migration"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*70)
        print("MIGRATION: Add Entry-Level Template Sharing")
        print("="*70)
        
        # ================================================================
        # Part 1: Check if source_entry_id column exists
        # ================================================================
        cursor.execute("PRAGMA table_info(TemplateRelationshipSharing)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'source_entry_id' in columns:
            print("✓ Column source_entry_id already exists. Skipping migration.")
            return
        
        # ================================================================
        # Part 2: Recreate table with new schema
        # ================================================================
        # SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table
        
        print("\n[Step 1] Creating temporary table with new schema...")
        cursor.execute("""
            CREATE TABLE TemplateRelationshipSharing_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_entry_id INTEGER NOT NULL,
                relationship_definition_id INTEGER NOT NULL,
                source_entry_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
                FOREIGN KEY (source_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                UNIQUE(template_entry_id, relationship_definition_id, source_entry_id)
            )
        """)
        print("    ✓ Created new table schema")
        print("    Added: source_entry_id column (nullable)")
        print("    Updated: UNIQUE constraint to include source_entry_id")
        
        # ================================================================
        # Part 3: Copy existing data
        # ================================================================
        print("\n[Step 2] Copying existing data...")
        cursor.execute("""
            INSERT INTO TemplateRelationshipSharing_new 
                (id, template_entry_id, relationship_definition_id, created_at)
            SELECT 
                id, template_entry_id, relationship_definition_id, created_at
            FROM TemplateRelationshipSharing
        """)
        rows_copied = cursor.rowcount
        print(f"    ✓ Copied {rows_copied} existing sharing configurations")
        print(f"    Note: target_entry_id will be NULL for existing records")
        print(f"          (meaning share with ALL entries of that relationship type)")
        
        # ================================================================
        # Part 4: Replace old table with new table
        # ================================================================
        print("\n[Step 3] Replacing old table...")
        cursor.execute("DROP TABLE TemplateRelationshipSharing")
        cursor.execute("ALTER TABLE TemplateRelationshipSharing_new RENAME TO TemplateRelationshipSharing")
        print("    ✓ Table replaced successfully")
        
        # ================================================================
        # Part 5: Commit changes
        # ================================================================
        conn.commit()
        
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nSchema Changes:")
        print("  • TemplateRelationshipSharing.source_entry_id added (INTEGER, nullable)")
        print("  • UNIQUE constraint updated: (template_entry_id, relationship_definition_id, source_entry_id)")
        print("\nData Migration:")
        print(f"  • {rows_copied} existing records preserved with source_entry_id = NULL")
        print("  • NULL source_entry_id = share with all entries of that relationship type")
        print("  • Non-NULL source_entry_id = share with entries linked to specific parent entry")
        print("\n")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: Migration failed: {e}", file=sys.stderr)
        raise

if __name__ == '__main__':
    migrate()
