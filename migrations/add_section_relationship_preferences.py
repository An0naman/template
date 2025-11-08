"""
Migration: Add Section-Level Relationship Preferences Table

This migration creates a table to store section-level configuration for relationship sections.
Configuration includes:
- Which relationship definitions are hidden
- Filter preferences for each relationship definition

Configuration is stored at the section DEFINITION level (entry_type_id + section_order.id),
meaning all entries of the same type share the same configuration.
"""

import sqlite3
import os

def run_migration():
    """Create section_relationship_preferences table"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'template.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating section_relationship_preferences table...")
    
    # Create the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section_relationship_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            relationship_definition_id INTEGER NOT NULL,
            is_hidden BOOLEAN DEFAULT 0,
            filter_status_category TEXT,
            filter_specific_states TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_type_id) REFERENCES entry_types (id) ON DELETE CASCADE,
            FOREIGN KEY (section_id) REFERENCES section_order (id) ON DELETE CASCADE,
            FOREIGN KEY (relationship_definition_id) REFERENCES relationship_definitions (id) ON DELETE CASCADE,
            UNIQUE(entry_type_id, section_id, relationship_definition_id)
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_section_rel_prefs_lookup 
        ON section_relationship_preferences(entry_type_id, section_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_section_rel_prefs_relationship 
        ON section_relationship_preferences(relationship_definition_id)
    """)
    
    conn.commit()
    print("✅ section_relationship_preferences table created successfully")
    print("✅ Indexes created successfully")
    
    # Show table info
    cursor.execute("PRAGMA table_info(section_relationship_preferences)")
    columns = cursor.fetchall()
    print("\nTable structure:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

if __name__ == '__main__':
    run_migration()
