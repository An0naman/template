#!/usr/bin/env python3
"""
Migration script to add section styles support to existing theme settings.
This script adds the new section_styles parameters to existing installations.
"""

import sqlite3
import json
import os
import sys
from pathlib import Path

def get_database_path():
    """Get the database path, checking multiple possible locations"""
    possible_paths = [
        'data/template.db',
        'template.db',
        'data/app.db',
        'app.db',
        'instance/app.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print("Warning: No database found. Creating default template.db")
    return 'template.db'

def migrate_section_styles():
    """Add section styles support to the database"""
    
    db_path = get_database_path()
    print(f"Using database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if SystemParameters table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SystemParameters'
        """)
        
        if not cursor.fetchone():
            print("SystemParameters table not found. Creating it...")
            cursor.execute("""
                CREATE TABLE SystemParameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parameter_name TEXT UNIQUE NOT NULL,
                    parameter_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("SystemParameters table created successfully.")
        
        # Check if section styles parameter already exists
        cursor.execute("""
            SELECT parameter_value FROM SystemParameters 
            WHERE parameter_name = 'theme_section_styles'
        """)
        
        existing_section_styles = cursor.fetchone()
        
        if existing_section_styles:
            print("Section styles parameter already exists.")
            try:
                current_styles = json.loads(existing_section_styles[0])
                print(f"Current section styles: {current_styles}")
            except (json.JSONDecodeError, TypeError):
                print("Invalid JSON in existing section styles, will reset to defaults.")
                existing_section_styles = None
        
        if not existing_section_styles:
            # Add default section styles
            default_section_styles = {
                'border_style': 'rounded',
                'spacing': 'normal',
                'background': 'subtle'
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value)
                VALUES ('theme_section_styles', ?)
            """, (json.dumps(default_section_styles),))
            
            print("Added default section styles:")
            print(f"  Border Style: {default_section_styles['border_style']}")
            print(f"  Spacing: {default_section_styles['spacing']}")
            print(f"  Background: {default_section_styles['background']}")
        
        # Show current theme settings
        cursor.execute("""
            SELECT parameter_name, parameter_value FROM SystemParameters 
            WHERE parameter_name LIKE 'theme_%'
            ORDER BY parameter_name
        """)
        
        theme_settings = cursor.fetchall()
        
        if theme_settings:
            print("\nCurrent theme settings:")
            for param_name, param_value in theme_settings:
                if param_name == 'theme_section_styles':
                    try:
                        styles = json.loads(param_value)
                        print(f"  {param_name}: {styles}")
                    except (json.JSONDecodeError, TypeError):
                        print(f"  {param_name}: {param_value} (invalid JSON)")
                else:
                    print(f"  {param_name}: {param_value}")
        else:
            print("\nNo theme settings found.")
        
        # Commit changes
        conn.commit()
        print("\nSection styles migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def main():
    """Main migration function"""
    print("Section Styles Migration")
    print("=" * 50)
    print("This script adds section styling support to your theme settings.")
    print("This includes border styles, spacing options, and background effects.\n")
    
    # Run migration
    success = migrate_section_styles()
    
    if success:
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("\nYou can now access section styling options in:")
        print("Settings → System Configuration → System Theme → Section Styling")
        print("\nAvailable options:")
        print("• Border Style: rounded, sharp, subtle, bold")
        print("• Section Spacing: compact, normal, spacious")
        print("• Background Style: flat, subtle, elevated, glassmorphic")
    else:
        print("\n" + "=" * 50)
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
