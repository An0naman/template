#!/usr/bin/env python3
"""
Migration script to add default search parameters to SystemParameters table
"""

import sqlite3
import os
import sys

def migrate_search_defaults():
    """Add default search parameters to SystemParameters table"""
    
    # Get the project root directory (where run.py is located)
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(project_root, 'data', 'template.db')
    
    print(f"🔧 Adding default search parameters to database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at {db_path}")
        print("   Make sure you have initialized the database by running the app first.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if SystemParameters table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SystemParameters'
        """)
        
        if not cursor.fetchone():
            print("❌ SystemParameters table not found! Please ensure the database is properly initialized.")
            return False
        
        # Define the new search parameters to add
        search_params = {
            'default_search_term': '',
            'default_type_filter': '',
            'default_status_filter': '',
            'default_date_range': '',
            'default_sort_by': 'created_desc',
            'default_content_display': '',
            'default_result_limit': '50'
        }
        
        added_count = 0
        updated_count = 0
        
        for param_name, default_value in search_params.items():
            # Check if parameter already exists
            cursor.execute("""
                SELECT COUNT(*) FROM SystemParameters 
                WHERE parameter_name = ?
            """, (param_name,))
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"✅ {param_name} already exists in database.")
                updated_count += 1
            else:
                print(f"📝 Adding {param_name}...")
                
                # Add the new parameter
                cursor.execute("""
                    INSERT INTO SystemParameters (parameter_name, parameter_value)
                    VALUES (?, ?)
                """, (param_name, default_value))
                
                added_count += 1
        
        if added_count > 0:
            conn.commit()
            print(f"✅ Added {added_count} new search parameters!")
        
        if updated_count > 0:
            print(f"✅ {updated_count} search parameters already existed.")
        
        # Show current search parameters for verification
        print("\n📋 Current Search Default Parameters:")
        cursor.execute("""
            SELECT parameter_name, parameter_value FROM SystemParameters 
            WHERE parameter_name LIKE 'default_%'
            ORDER BY parameter_name
        """)
        
        for row in cursor.fetchall():
            value_display = f"'{row['parameter_value']}'" if row['parameter_value'] else '(empty)'
            print(f"   {row['parameter_name']}: {value_display}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🚀 Search Defaults Migration")
    print("=" * 50)
    
    success = migrate_search_defaults()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📝 What was changed:")
        print("   • Added default search parameters to SystemParameters table")
        print("   • Search filters will now be saved to database instead of localStorage")
        print("\n🎯 Features:")
        print("   • Search parameters persist across browsers and devices")
        print("   • Can be managed through system settings")
        print("   • Automatically saved when filters are applied")
        print("   • API endpoints: GET/POST /api/search_defaults")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
