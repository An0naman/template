#!/usr/bin/env python3
"""
Migration: Add Tab Support to Entry Layout System

This migration adds support for organizing entry sections into tabs.
Each entry type layout can have multiple tabs, and sections are assigned to specific tabs.

Tables modified:
- EntryLayoutSection: Add tab_id and tab_order columns
- EntryLayoutTab: New table for tab configuration

Changes:
1. Create EntryLayoutTab table
2. Add tab_id column to EntryLayoutSection
3. Add tab_order column to EntryLayoutSection
4. Create default 'main' tab for all existing layouts
5. Assign all existing sections to 'main' tab
"""

import sqlite3
import json
import sys
import os

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template.db')


def migrate():
    """Run the migration to add tab support"""
    
    print("=" * 70)
    print("Starting Entry Layout Tab Support Migration")
    print("=" * 70)
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Step 1: Create EntryLayoutTab table
        print("\n[1/5] Creating EntryLayoutTab table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryLayoutTab (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layout_id INTEGER NOT NULL,
                tab_id TEXT NOT NULL,
                tab_label TEXT NOT NULL,
                tab_icon TEXT DEFAULT 'fa-folder',
                display_order INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (layout_id) REFERENCES EntryTypeLayout(id) ON DELETE CASCADE,
                UNIQUE(layout_id, tab_id)
            );
        ''')
        print("✓ EntryLayoutTab table created successfully")
        
        # Step 2: Add tab_id column to EntryLayoutSection
        print("\n[2/5] Adding tab_id column to EntryLayoutSection...")
        try:
            cursor.execute("PRAGMA table_info(EntryLayoutSection)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'tab_id' not in columns:
                cursor.execute('''
                    ALTER TABLE EntryLayoutSection 
                    ADD COLUMN tab_id TEXT DEFAULT 'main'
                ''')
                print("✓ tab_id column added to EntryLayoutSection")
            else:
                print("⊙ tab_id column already exists")
        except sqlite3.Error as e:
            print(f"✗ Error adding tab_id column: {e}")
            raise
        
        # Step 3: Add tab_order column to EntryLayoutSection
        print("\n[3/5] Adding tab_order column to EntryLayoutSection...")
        try:
            cursor.execute("PRAGMA table_info(EntryLayoutSection)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'tab_order' not in columns:
                cursor.execute('''
                    ALTER TABLE EntryLayoutSection 
                    ADD COLUMN tab_order INTEGER DEFAULT 0
                ''')
                print("✓ tab_order column added to EntryLayoutSection")
            else:
                print("⊙ tab_order column already exists")
        except sqlite3.Error as e:
            print(f"✗ Error adding tab_order column: {e}")
            raise
        
        # Step 4: Create default 'main' tab for all existing layouts
        print("\n[4/5] Creating default 'main' tab for existing layouts...")
        cursor.execute("SELECT id FROM EntryTypeLayout")
        layouts = cursor.fetchall()
        
        if layouts:
            created_count = 0
            for layout in layouts:
                layout_id = layout['id']
                
                # Check if 'main' tab already exists
                cursor.execute('''
                    SELECT id FROM EntryLayoutTab 
                    WHERE layout_id = ? AND tab_id = 'main'
                ''', (layout_id,))
                
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO EntryLayoutTab (
                            layout_id, tab_id, tab_label, tab_icon, display_order, is_visible
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (layout_id, 'main', 'Overview', 'fa-home', 0, 1))
                    created_count += 1
            
            print(f"✓ Created {created_count} default 'main' tabs")
        else:
            print("⊙ No existing layouts found")
        
        # Step 5: Update existing sections to use 'main' tab
        print("\n[5/5] Assigning existing sections to 'main' tab...")
        cursor.execute('''
            UPDATE EntryLayoutSection 
            SET tab_id = 'main', tab_order = display_order
            WHERE tab_id IS NULL OR tab_id = ''
        ''')
        updated_count = cursor.rowcount
        print(f"✓ Updated {updated_count} sections to use 'main' tab")
        
        # Create indexes
        print("\n[Bonus] Creating indexes for performance...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_entry_layout_tab_layout 
            ON EntryLayoutTab(layout_id);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_entry_layout_section_tab 
            ON EntryLayoutSection(tab_id);
        ''')
        print("✓ Indexes created successfully")
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✓ Migration completed successfully!")
        print("=" * 70)
        print("\nChanges applied:")
        print("  ✓ Created EntryLayoutTab table")
        print("  ✓ Added tab_id column to EntryLayoutSection")
        print("  ✓ Added tab_order column to EntryLayoutSection")
        print("  ✓ Created default 'main' tabs for all layouts")
        print("  ✓ Assigned existing sections to 'main' tab")
        print("\nNext steps:")
        print("  1. Restart your Flask application")
        print("  2. Navigate to Entry Layout Builder")
        print("  3. Create new tabs and organize sections across tabs")
        print("  4. View entry detail pages with tabbed layout")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            conn.close()


def rollback():
    """Rollback the migration (for development/testing)"""
    
    print("=" * 70)
    print("Rolling back Entry Layout Tab Support Migration")
    print("=" * 70)
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n[1/4] Dropping indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_layout_tab_layout")
        cursor.execute("DROP INDEX IF EXISTS idx_entry_layout_section_tab")
        print("✓ Indexes dropped")
        
        print("\n[2/4] Dropping EntryLayoutTab table...")
        cursor.execute("DROP TABLE IF EXISTS EntryLayoutTab")
        print("✓ EntryLayoutTab table dropped")
        
        print("\n[3/4] Removing tab_id column from EntryLayoutSection...")
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        print("  Note: SQLite doesn't support DROP COLUMN. Columns will remain but be unused.")
        print("  Consider manually recreating the table if needed.")
        
        print("\n[4/4] Removing tab_order column from EntryLayoutSection...")
        print("  Note: SQLite doesn't support DROP COLUMN. Columns will remain but be unused.")
        print("  Consider manually recreating the table if needed.")
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✓ Rollback completed!")
        print("=" * 70)
        print("\nNote: Due to SQLite limitations, tab_id and tab_order columns")
        print("remain in EntryLayoutSection but are no longer used.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Rollback failed: {e}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Entry Layout Tab Support Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
