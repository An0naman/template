#!/usr/bin/env python3
"""
Database migration script to add theme settings support.
This script adds the necessary system_params entries for theme functionality.
"""

import sqlite3
import os
import sys

def migrate_theme_settings():
    """Add theme settings to system_params table"""
    
    # Database path
    db_path = 'template.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if SystemParameters table exists, if not create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SystemParameters (
                parameter_name TEXT PRIMARY KEY,
                parameter_value TEXT
            )
        """)
        
        # Default theme settings
        theme_settings = [
            ('theme_color_scheme', 'default'),
            ('theme_dark_mode', 'false'),
            ('theme_font_size', 'normal'),
            ('theme_high_contrast', 'false')
        ]
        
        # Insert theme settings if they don't exist
        for parameter_name, parameter_value in theme_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value)
                VALUES (?, ?)
            """, (parameter_name, parameter_value))
            
            # Check if it was inserted or already existed
            cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (parameter_name,))
            current_value = cursor.fetchone()[0]
            
            if current_value:
                print(f"✓ Theme setting '{parameter_name}' = '{current_value}'")
            else:
                print(f"✗ Failed to set theme setting '{parameter_name}'")
        
        conn.commit()
        print("\n✅ Theme settings migration completed successfully!")
        
        # Display current theme settings
        print("\nCurrent theme settings:")
        cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters WHERE parameter_name LIKE 'theme_%'")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_migration():
    """Verify that theme settings were added correctly"""
    try:
        conn = sqlite3.connect('template.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM SystemParameters WHERE parameter_name LIKE 'theme_%'")
        count = cursor.fetchone()[0]
        
        if count >= 4:
            print(f"✅ Verification successful: {count} theme settings found")
            return True
        else:
            print(f"❌ Verification failed: Only {count} theme settings found (expected 4)")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🎨 Theme Settings Database Migration")
    print("=" * 40)
    
    if migrate_theme_settings():
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Migration may have issues. Please check manually.")
            sys.exit(1)
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
