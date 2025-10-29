#!/usr/bin/env python3
"""
Migration: Add Milestone Templates Support
Creates the EntryTypeRelationship table and adds template fields to Entry table
for enabling milestone template sharing between related entry types.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_connection():
    """Get direct database connection without Flask context"""
    # Import here to avoid Flask app creation
    import os
    db_path = os.environ.get('DATABASE_PATH', 'data/template.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    """Add milestone template support"""
    print("\n" + "=" * 60)
    print("MIGRATION: Add Milestone Templates")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ================================================================
        # Part 1: Add template fields to Entry table
        # ================================================================
        print("Part 1: Adding template fields to Entry table...")
        
        # Check current Entry table schema
        cursor.execute("PRAGMA table_info(Entry)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        print(f"Current Entry table has {len(columns)} columns")
        
        # Add is_milestone_template column
        if 'is_milestone_template' not in columns:
            print("  - Adding is_milestone_template column...")
            cursor.execute("""
                ALTER TABLE Entry 
                ADD COLUMN is_milestone_template BOOLEAN DEFAULT 0
            """)
            print("    ✓ Added is_milestone_template")
        else:
            print("  - is_milestone_template column already exists")
        
        # Add template_name column
        if 'template_name' not in columns:
            print("  - Adding template_name column...")
            cursor.execute("""
                ALTER TABLE Entry 
                ADD COLUMN template_name TEXT
            """)
            print("    ✓ Added template_name")
        else:
            print("  - template_name column already exists")
        
        # Add template_description column
        if 'template_description' not in columns:
            print("  - Adding template_description column...")
            cursor.execute("""
                ALTER TABLE Entry 
                ADD COLUMN template_description TEXT
            """)
            print("    ✓ Added template_description")
        else:
            print("  - template_description column already exists")
        
        # Add template_distribution_status column
        if 'template_distribution_status' not in columns:
            print("  - Adding template_distribution_status column...")
            cursor.execute("""
                ALTER TABLE Entry 
                ADD COLUMN template_distribution_status TEXT DEFAULT 'private'
            """)
            print("    ✓ Added template_distribution_status")
        else:
            print("  - template_distribution_status column already exists")
        
        # ================================================================
        # Part 2: Create EntryTypeRelationship table
        # ================================================================
        print("\nPart 2: Creating EntryTypeRelationship table...")
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='EntryTypeRelationship'
        """)
        
        if cursor.fetchone():
            print("  - EntryTypeRelationship table already exists")
        else:
            print("  - Creating EntryTypeRelationship table...")
            cursor.execute("""
                CREATE TABLE EntryTypeRelationship (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_entry_type_id INTEGER NOT NULL,
                    to_entry_type_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL CHECK(
                        relationship_type IN ('template_source', 'template_target', 'bidirectional')
                    ),
                    can_share_templates BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
                    UNIQUE(from_entry_type_id, to_entry_type_id)
                )
            """)
            print("    ✓ Created EntryTypeRelationship table")
            
            # Create indexes for better query performance
            print("  - Creating indexes...")
            cursor.execute("""
                CREATE INDEX idx_entry_type_rel_from 
                ON EntryTypeRelationship(from_entry_type_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_entry_type_rel_to 
                ON EntryTypeRelationship(to_entry_type_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_entry_type_rel_can_share 
                ON EntryTypeRelationship(can_share_templates)
            """)
            print("    ✓ Created indexes")
        
        # ================================================================
        # Part 3: Add index for template discovery
        # ================================================================
        print("\nPart 3: Creating indexes for template discovery...")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entry_is_template 
                ON Entry(is_milestone_template, template_distribution_status)
            """)
            print("  ✓ Created index on Entry for template queries")
        except Exception as e:
            print(f"  - Index may already exist: {e}")
        
        # Commit all changes
        conn.commit()
        
        # ================================================================
        # Verification
        # ================================================================
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
        # Verify Entry table structure
        cursor.execute("PRAGMA table_info(Entry)")
        entry_columns = cursor.fetchall()
        print("\nUpdated Entry table columns:")
        for col in entry_columns:
            if col[1] in ['is_milestone_template', 'template_name', 
                          'template_description', 'template_distribution_status']:
                print(f"  ✓ {col[1]}: {col[2]}")
        
        # Verify EntryTypeRelationship table
        cursor.execute("PRAGMA table_info(EntryTypeRelationship)")
        rel_columns = cursor.fetchall()
        print("\nEntryTypeRelationship table structure:")
        for col in rel_columns:
            print(f"  - {col[1]}: {col[2]}")
        
        # Show indexes
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' 
            AND (name LIKE '%entry_type_rel%' OR name LIKE '%entry_is_template%')
        """)
        indexes = cursor.fetchall()
        print("\nCreated indexes:")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        print("\n" + "=" * 60)
        print("✓ Milestone Templates feature is now available!")
        print("=" * 60)
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error during migration: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()


def rollback():
    """Remove milestone template support (for development/testing)"""
    print("\n" + "=" * 60)
    print("ROLLBACK: Remove Milestone Templates")
    print("=" * 60 + "\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("⚠️  WARNING: This will remove all milestone template data!")
        print("⚠️  Template configurations will be permanently lost!")
        
        # Drop EntryTypeRelationship table
        print("\nDropping EntryTypeRelationship table...")
        cursor.execute("DROP TABLE IF EXISTS EntryTypeRelationship")
        print("  ✓ Dropped EntryTypeRelationship table")
        
        # Drop indexes
        print("\nDropping indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_type_rel_from")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_type_rel_to")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_type_rel_can_share")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_is_template")
        print("  ✓ Dropped indexes")
        
        # Note: SQLite doesn't support dropping columns easily
        # Template columns in Entry table will remain but be unused
        print("\n⚠️  Note: Template columns in Entry table cannot be easily removed")
        print("  (is_milestone_template, template_name, template_description, template_distribution_status)")
        print("  These columns will remain in the database but will be ignored.")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ Rollback completed!")
        print("=" * 60)
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error during rollback: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Milestone Templates Migration')
    parser.add_argument('--rollback', action='store_true', 
                       help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
