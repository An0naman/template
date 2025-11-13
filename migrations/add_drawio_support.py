#!/usr/bin/env python3
"""
Migration: Add Draw.io Diagram Support

This migration adds:
1. EntryDrawioDiagram table for storing diagram XML data
2. 'drawio' section to existing entry type layouts
"""

import sqlite3
import json
import sys
import os

# Database path (same as in app/config.py)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template.db')


def migrate():
    """Run the migration to add Draw.io support"""
    
    print("=" * 60)
    print("Starting Draw.io Diagram Support Migration")
    print("=" * 60)
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create EntryDrawioDiagram Table
        print("\n[1/3] Creating EntryDrawioDiagram table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryDrawioDiagram (
                entry_id INTEGER PRIMARY KEY,
                diagram_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
            );
        ''')
        print("✓ EntryDrawioDiagram table created successfully")
        
        # Add drawio section to existing layouts
        print("\n[2/3] Adding Draw.io section to existing entry type layouts...")
        
        # Get all existing entry type layouts
        cursor.execute("SELECT id, entry_type_id FROM EntryTypeLayout")
        layouts = cursor.fetchall()
        
        if layouts:
            added_count = 0
            for layout in layouts:
                layout_id = layout['id']
                entry_type_id = layout['entry_type_id']
                
                # Check if drawio section already exists
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM EntryLayoutSection 
                    WHERE layout_id = ? AND section_type = 'drawio'
                """, (layout_id,))
                
                if cursor.fetchone()['count'] == 0:
                    # Find the max position_y to place the new section after all others
                    cursor.execute("""
                        SELECT MAX(position_y) as max_y 
                        FROM EntryLayoutSection 
                        WHERE layout_id = ?
                    """, (layout_id,))
                    
                    max_y_result = cursor.fetchone()
                    max_y = max_y_result['max_y'] if max_y_result['max_y'] is not None else 0
                    new_position_y = max_y + 4  # Place it 4 rows below the last section
                    
                    # Find the max display_order
                    cursor.execute("""
                        SELECT MAX(display_order) as max_order 
                        FROM EntryLayoutSection 
                        WHERE layout_id = ?
                    """, (layout_id,))
                    
                    max_order_result = cursor.fetchone()
                    max_order = max_order_result['max_order'] if max_order_result['max_order'] is not None else 0
                    new_display_order = max_order + 1
                    
                    # Insert drawio section
                    config = json.dumps({
                        'theme': 'auto',
                        'toolbar': True,
                        'save_automatically': True
                    })
                    
                    cursor.execute("""
                        INSERT INTO EntryLayoutSection (
                            layout_id, section_type, title, 
                            position_x, position_y, width, height,
                            is_visible, is_collapsible, default_collapsed,
                            config, display_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        layout_id, 'drawio', 'Draw.io Diagram',
                        0, new_position_y, 12, 6,
                        0, 1, 0,
                        config, new_display_order
                    ))
                    
                    added_count += 1
                    print(f"  ✓ Added Draw.io section to layout for entry type {entry_type_id}")
            
            print(f"\n✓ Added Draw.io section to {added_count} layout(s)")
        else:
            print("  ⊙ No existing layouts found")
        
        conn.commit()
        
        print("\n[3/3] Verifying migration...")
        
        # Check if table exists and has correct structure
        cursor.execute("PRAGMA table_info(EntryDrawioDiagram)")
        columns = [col['name'] for col in cursor.fetchall()]
        expected_columns = ['entry_id', 'diagram_data', 'created_at', 'updated_at']
        
        if all(col in columns for col in expected_columns):
            print("✓ EntryDrawioDiagram table structure verified")
        else:
            print("⚠ Warning: EntryDrawioDiagram table structure may be incomplete")
        
        # Count how many layouts now have drawio section
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM EntryLayoutSection 
            WHERE section_type = 'drawio'
        """)
        drawio_count = cursor.fetchone()['count']
        print(f"✓ {drawio_count} layout(s) now have Draw.io section")
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nNew features added:")
        print("  - EntryDrawioDiagram table for storing diagram data")
        print("  - Draw.io section added to all existing entry type layouts")
        print("\nNext steps:")
        print("  1. Restart your Flask application")
        print("  2. Navigate to any entry type's layout builder")
        print("  3. Make the Draw.io section visible if desired")
        print("  4. Create diagrams directly in your entry detail pages!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


def rollback():
    """Rollback the migration (for development/testing)"""
    
    print("=" * 60)
    print("Rolling back Draw.io Diagram Support Migration")
    print("=" * 60)
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("\n[1/2] Removing Draw.io sections from layouts...")
        cursor.execute("DELETE FROM EntryLayoutSection WHERE section_type = 'drawio'")
        deleted_sections = cursor.rowcount
        print(f"✓ Removed {deleted_sections} Draw.io section(s)")
        
        print("\n[2/2] Dropping EntryDrawioDiagram table...")
        cursor.execute("DROP TABLE IF EXISTS EntryDrawioDiagram")
        print("✓ EntryDrawioDiagram table dropped")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ Rollback completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Rollback failed: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Draw.io Diagram Support Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
