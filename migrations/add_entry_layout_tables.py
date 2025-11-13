#!/usr/bin/env python3
"""
Migration: Add Entry Layout Builder Tables

This migration adds support for configurable entry layouts at the entry type level.
Similar to the Dashboard Builder, but for entry detail page layouts.

Tables created:
- EntryTypeLayout: Stores layout configuration per entry type
- EntryLayoutSection: Stores individual section configurations
"""

import sqlite3
import json
import sys
import os

# Database path (same as in app/config.py)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template.db')

# Default section configurations based on common entry detail sections
DEFAULT_SECTIONS = {
    'header': {
        'title': 'Entry Details',
        'section_type': 'header',
        'position_x': 0,
        'position_y': 0,
        'width': 12,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 0,
        'default_collapsed': 0,
        'display_order': 1,
        'config': {
            'show_dates': True,
            'show_status': True,
            'show_description': True
        }
    },
    'notes': {
        'title': 'Notes',
        'section_type': 'notes',
        'position_x': 0,
        'position_y': 3,
        'width': 6,
        'height': 4,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 2,
        'config': {
            'default_note_type': 'General',
            'show_note_relationships': True,
            'display_mode': 'list'
        }
    },
    'relationships': {
        'title': 'Relationships',
        'section_type': 'relationships',
        'position_x': 6,
        'position_y': 3,
        'width': 6,
        'height': 4,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 3,
        'config': {
            'show_add_button': True,
            'group_by_type': True
        }
    },
    'labels': {
        'title': 'Labels',
        'section_type': 'labels',
        'position_x': 0,
        'position_y': 7,
        'width': 12,
        'height': 2,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 4,
        'config': {}
    },
    'sensors': {
        'title': 'Sensor Data',
        'section_type': 'sensors',
        'position_x': 0,
        'position_y': 9,
        'width': 12,
        'height': 5,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 5,
        'config': {
            'default_chart_type': 'line',
            'default_time_range': '7d',
            'chart_height': 300
        }
    },
    'reminders': {
        'title': 'Reminders',
        'section_type': 'reminders',
        'position_x': 0,
        'position_y': 14,
        'width': 12,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 6,
        'config': {}
    },
    'ai_assistant': {
        'title': 'AI Assistant',
        'section_type': 'ai_assistant',
        'position_x': 0,
        'position_y': 17,
        'width': 12,
        'height': 4,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 1,
        'display_order': 7,
        'config': {
            'auto_open': False
        }
    },
    'attachments': {
        'title': 'Attachments',
        'section_type': 'attachments',
        'position_x': 0,
        'position_y': 21,
        'width': 6,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 8,
        'config': {}
    },
    'form_fields': {
        'title': 'Custom Fields',
        'section_type': 'form_fields',
        'position_x': 6,
        'position_y': 21,
        'width': 6,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 9,
        'config': {}
    },
    'qr_code': {
        'title': 'QR Code',
        'section_type': 'qr_code',
        'position_x': 0,
        'position_y': 24,
        'width': 4,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 1,
        'display_order': 10,
        'config': {}
    },
    'label_printing': {
        'title': 'Label Printing',
        'section_type': 'label_printing',
        'position_x': 4,
        'position_y': 24,
        'width': 8,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 1,
        'display_order': 11,
        'config': {}
    },
    'relationship_opportunities': {
        'title': 'Shared Relationships',
        'section_type': 'relationship_opportunities',
        'position_x': 0,
        'position_y': 27,
        'width': 12,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 1,
        'display_order': 12,
        'config': {}
    },
    'timeline': {
        'title': 'Progress Timeline',
        'section_type': 'timeline',
        'position_x': 0,
        'position_y': 30,
        'width': 12,
        'height': 3,
        'is_visible': 1,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 13,
        'config': {}
    },
    'drawio': {
        'title': 'Draw.io Diagram',
        'section_type': 'drawio',
        'position_x': 0,
        'position_y': 33,
        'width': 12,
        'height': 6,
        'is_visible': 0,
        'is_collapsible': 1,
        'default_collapsed': 0,
        'display_order': 14,
        'config': {
            'theme': 'auto',
            'toolbar': True,
            'save_automatically': True
        }
    }
}


def create_default_layout_for_entry_type(cursor, entry_type_id, entry_type_data):
    """Create default layout configuration for an entry type"""
    
    # Create layout record
    layout_config = json.dumps({'cols': 12, 'rowHeight': 80})
    
    cursor.execute("""
        INSERT INTO EntryTypeLayout (entry_type_id, layout_config)
        VALUES (?, ?)
    """, (entry_type_id, layout_config))
    
    layout_id = cursor.lastrowid
    
    # Determine which sections to include based on entry type settings
    sections_to_add = ['header', 'notes', 'relationships', 'attachments']
    
    # Add labels if enabled for this entry type
    if entry_type_data.get('show_labels_section', 1):
        sections_to_add.append('labels')
    
    # Add sensors if enabled for this entry type
    if entry_type_data.get('has_sensors', 0):
        sections_to_add.append('sensors')
    
    # Add other common sections
    sections_to_add.extend([
        'reminders',
        'ai_assistant',
        'form_fields',
        'qr_code',
        'label_printing',
        'relationship_opportunities',
        'timeline'
    ])
    
    # Create section records
    for section_key in sections_to_add:
        if section_key in DEFAULT_SECTIONS:
            section_data = DEFAULT_SECTIONS[section_key]
            
            # Adjust visibility based on entry type settings
            is_visible = section_data['is_visible']
            
            if section_key == 'labels' and not entry_type_data.get('show_labels_section', 1):
                is_visible = 0
            elif section_key == 'sensors' and not entry_type_data.get('has_sensors', 0):
                is_visible = 0
            
            cursor.execute("""
                INSERT INTO EntryLayoutSection (
                    layout_id, section_type, title, position_x, position_y,
                    width, height, is_visible, is_collapsible, default_collapsed,
                    config, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                layout_id,
                section_data['section_type'],
                section_data['title'],
                section_data['position_x'],
                section_data['position_y'],
                section_data['width'],
                section_data['height'],
                is_visible,
                section_data['is_collapsible'],
                section_data['default_collapsed'],
                json.dumps(section_data['config']),
                section_data['display_order']
            ))
    
    return layout_id


def migrate():
    """Run the migration to add entry layout tables"""
    
    print("=" * 60)
    print("Starting Entry Layout Builder Migration")
    print("=" * 60)
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create EntryTypeLayout Table
        print("\n[1/4] Creating EntryTypeLayout table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryTypeLayout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type_id INTEGER NOT NULL UNIQUE,
                layout_config TEXT DEFAULT '{"cols": 12, "rowHeight": 80}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
            );
        ''')
        print("✓ EntryTypeLayout table created successfully")
        
        # Create EntryLayoutSection Table
        print("\n[2/4] Creating EntryLayoutSection table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryLayoutSection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layout_id INTEGER NOT NULL,
                section_type TEXT NOT NULL,
                title TEXT,
                position_x INTEGER DEFAULT 0,
                position_y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 12,
                height INTEGER DEFAULT 2,
                is_visible INTEGER DEFAULT 1,
                is_collapsible INTEGER DEFAULT 1,
                default_collapsed INTEGER DEFAULT 0,
                config TEXT DEFAULT '{}',
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (layout_id) REFERENCES EntryTypeLayout(id) ON DELETE CASCADE
            );
        ''')
        print("✓ EntryLayoutSection table created successfully")
        
        # Create indexes for performance
        print("\n[3/4] Creating indexes...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_entry_type_layout_entry_type 
            ON EntryTypeLayout(entry_type_id);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_entry_layout_section_layout 
            ON EntryLayoutSection(layout_id);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_entry_layout_section_type 
            ON EntryLayoutSection(section_type);
        ''')
        print("✓ Indexes created successfully")
        
        # Generate default layouts for existing entry types
        print("\n[4/4] Generating default layouts for existing entry types...")
        
        # Check if EntryType table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='EntryType'
        """)
        
        table_exists = cursor.fetchone()
        if not table_exists:
            print("  ⊙ EntryType table doesn't exist yet - skipping default layout creation")
            print("  ℹ Default layouts will be created automatically when entry types are added")
        else:
            cursor.execute("""
                SELECT id, name, has_sensors, show_labels_section, show_end_dates
                FROM EntryType
            """)
            
            entry_types = cursor.fetchall()
            
            if entry_types:
                print(f"Found {len(entry_types)} entry type(s)")
                
                for entry_type in entry_types:
                    entry_type_id = entry_type[0]
                    entry_type_name = entry_type[1]
                    
                    # Check if layout already exists
                    cursor.execute(
                        "SELECT id FROM EntryTypeLayout WHERE entry_type_id = ?",
                        (entry_type_id,)
                    )
                    
                    if cursor.fetchone() is None:
                        entry_type_data = {
                            'has_sensors': entry_type[2] if len(entry_type) > 2 else 0,
                            'show_labels_section': entry_type[3] if len(entry_type) > 3 else 1,
                            'show_end_dates': entry_type[4] if len(entry_type) > 4 else 0
                        }
                        
                        layout_id = create_default_layout_for_entry_type(
                            cursor, entry_type_id, entry_type_data
                        )
                        
                        # Count sections created
                        cursor.execute(
                            "SELECT COUNT(*) FROM EntryLayoutSection WHERE layout_id = ?",
                            (layout_id,)
                        )
                        section_count = cursor.fetchone()[0]
                        
                        print(f"  ✓ Created layout for '{entry_type_name}' with {section_count} sections")
                    else:
                        print(f"  ⊙ Layout already exists for '{entry_type_name}'")
            else:
                print("No entry types found. Layouts will be created when entry types are added.")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nNew tables created:")
        print("  - EntryTypeLayout: Stores layout configuration per entry type")
        print("  - EntryLayoutSection: Stores individual section configurations")
        print("\nNext steps:")
        print("  1. Restart your Flask application")
        print("  2. Navigate to Manage Entry Types")
        print("  3. Click 'Configure Layout' to customize entry layouts")
        print("=" * 60)
        
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
    
    print("=" * 60)
    print("Rolling back Entry Layout Builder Migration")
    print("=" * 60)
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n[1/2] Dropping EntryLayoutSection table...")
        cursor.execute("DROP TABLE IF EXISTS EntryLayoutSection")
        print("✓ EntryLayoutSection table dropped")
        
        print("\n[2/2] Dropping EntryTypeLayout table...")
        cursor.execute("DROP TABLE IF EXISTS EntryTypeLayout")
        print("✓ EntryTypeLayout table dropped")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓ Rollback completed successfully!")
        print("=" * 60)
        
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
    
    parser = argparse.ArgumentParser(description='Entry Layout Builder Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
