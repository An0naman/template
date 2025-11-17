#!/usr/bin/env python3
"""
Migration: Update default result limit from 50 to 10000

This migration updates the default result limit to support client-side filtering
on all entries rather than being limited to 50.

Changes:
- Updates SystemParameters.default_result_limit from '50' to '10000'
- Updates existing UserPreferences.default_result_limit from '50' to '10000'
"""

import sqlite3
import sys
import os

def run_migration(db_path):
    """Run the migration to update result limit defaults"""
    print(f"Running migration: update_result_limit_default.py")
    print(f"Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Update SystemParameters default
        cursor.execute("""
            UPDATE SystemParameters 
            SET parameter_value = '10000' 
            WHERE parameter_name = 'default_result_limit' 
            AND parameter_value = '50'
        """)
        system_params_updated = cursor.rowcount
        
        # Update UserPreferences for users who have the old default
        cursor.execute("""
            UPDATE UserPreferences 
            SET preference_value = '10000' 
            WHERE preference_name = 'default_result_limit' 
            AND preference_value = '50'
        """)
        user_prefs_updated = cursor.rowcount
        
        # Update SavedSearch result_limit defaults
        cursor.execute("""
            UPDATE SavedSearch 
            SET result_limit = '10000' 
            WHERE result_limit = '50'
        """)
        saved_searches_updated = cursor.rowcount
        
        conn.commit()
        
        print(f"  ✓ Updated SystemParameters: {system_params_updated} row(s)")
        print(f"  ✓ Updated UserPreferences: {user_prefs_updated} row(s)")
        print(f"  ✓ Updated SavedSearch: {saved_searches_updated} row(s)")
        print("  ✓ Migration completed successfully")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Migration failed: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python update_result_limit_default.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
    
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
