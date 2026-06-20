#!/usr/bin/env python3
"""
Migration script to add project_subtitle parameter to SystemParameters table
"""

import pymysql
import os
import sys

def migrate_project_subtitle():
    """Add project_subtitle parameter to SystemParameters table"""
    
    # Get the project root directory (where run.py is located)
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(project_root, 'data', 'template.db')
    
    print(f"🔧 Adding project_subtitle parameter to database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at {db_path}")
        print("   Make sure you have initialized the database by running the app first.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if SystemParameters table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SystemParameters'
        """)
        
        if not cursor.fetchone():
            print("❌ SystemParameters table not found! Please ensure the database is properly initialized.")
            return False
        
        # Check if project_subtitle parameter already exists
        cursor.execute("""
            SELECT COUNT(*) FROM SystemParameters 
            WHERE parameter_name = 'project_subtitle'
        """)
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("✅ project_subtitle parameter already exists in database.")
            
            # Show current value
            cursor.execute("""
                SELECT parameter_value FROM SystemParameters 
                WHERE parameter_name = 'project_subtitle'
            """)
            current_value = cursor.fetchone()[0]
            print(f"   Current value: '{current_value}'")
            
        else:
            print("📝 Adding project_subtitle parameter...")
            
            # Add the new parameter with default value
            cursor.execute("""
                INSERT INTO SystemParameters (parameter_name, parameter_value)
                VALUES ('project_subtitle', 'Management System')
            """)
            
            conn.commit()
            print("✅ project_subtitle parameter added successfully!")
            print("   Default value: 'Management System'")
        
        # Show current system parameters for verification
        print("\n📋 Current System Parameters:")
        cursor.execute("""
            SELECT parameter_name, parameter_value FROM SystemParameters 
            WHERE parameter_name IN ('project_name', 'project_subtitle', 'entry_singular_label', 'entry_plural_label')
            ORDER BY parameter_name
        """)
        
        for row in cursor.fetchall():
            print(f"   {row['parameter_name']}: '{row['parameter_value']}'")
        
        conn.close()
        return True
        
    except pymysql.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🚀 Project Subtitle Migration")
    print("=" * 50)
    
    success = migrate_project_subtitle()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📝 What was changed:")
        print("   • Added 'project_subtitle' parameter to SystemParameters table")
        print("   • Default value: 'Management System'")
        print("\n🎯 Next steps:")
        print("   • Visit Settings > General Settings to customize the project subtitle")
        print("   • The subtitle will appear under the project name on the main page")
        print("   • You can now set a custom subtitle instead of '<Entries> Management'")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
