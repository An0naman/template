#!/usr/bin/env python3
"""
Migration: Add template inheritance support to relationship definitions
Allows relationship types to enable template sharing between linked entries

Example: A "uses recipe" relationship can allow samples to inherit templates from their recipe
"""

import sqlite3
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_migration(db_path='data/template.db'):
    """Add template inheritance support via relationships"""
    
    print("=" * 80)
    print("MIGRATION: Add Relationship Template Inheritance Support")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # ================================================================
        # Part 1: Create TemplateRelationshipSharing table
        # ================================================================
        print("Part 1: Creating TemplateRelationshipSharing table...")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='TemplateRelationshipSharing'
        """)
        
        if cursor.fetchone():
            print("  - TemplateRelationshipSharing table already exists")
        else:
            print("  - Creating TemplateRelationshipSharing table...")
            cursor.execute("""
                CREATE TABLE TemplateRelationshipSharing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_entry_id INTEGER NOT NULL,
                    relationship_definition_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                    FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
                    UNIQUE(template_entry_id, relationship_definition_id)
                )
            """)
            print("    ✓ Created TemplateRelationshipSharing table")
            print("    This table defines which relationship types can access each template")
            
        # ================================================================
        # Part 2: Check current RelationshipDefinition table schema
        # ================================================================
        print("\nPart 2: Checking RelationshipDefinition table...")
        
        # Check current RelationshipDefinition table schema
        cursor.execute("PRAGMA table_info(RelationshipDefinition)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        print(f"Current RelationshipDefinition table has {len(columns)} columns")
        
        # Add allows_template_inheritance column
        if 'allows_template_inheritance' not in columns:
            print("  - Adding allows_template_inheritance column...")
            cursor.execute("""
                ALTER TABLE RelationshipDefinition 
                ADD COLUMN allows_template_inheritance BOOLEAN DEFAULT 0
            """)
            print("    ✓ Added allows_template_inheritance column")
            print("    This allows relationship types to enable template discovery")
            print("    Example: Samples can discover templates from their linked Recipe")
        else:
            print("  - allows_template_inheritance column already exists")
        
        # Add template_inheritance_direction column
        if 'template_inheritance_direction' not in columns:
            print("  - Adding template_inheritance_direction column...")
            cursor.execute("""
                ALTER TABLE RelationshipDefinition 
                ADD COLUMN template_inheritance_direction TEXT DEFAULT 'source_to_target'
                CHECK(template_inheritance_direction IN ('source_to_target', 'target_to_source', 'bidirectional'))
            """)
            print("    ✓ Added template_inheritance_direction column")
            print("    Values: 'source_to_target' (default), 'target_to_source', 'bidirectional'")
        else:
            print("  - template_inheritance_direction column already exists")
        
        conn.commit()
        
        print()
        print("=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("1. Configure relationship definitions to allow template inheritance")
        print("2. Example: Mark 'uses recipe' to allow samples to inherit recipe templates")
        print("3. Templates will now be discovered through entry relationships")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Migration failed: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/template.db'
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
