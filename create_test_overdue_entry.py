#!/usr/bin/env python3
"""
Test script to create a sample entry with an overdue intended end date
for testing the overdue notification functionality.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app
from app.db import get_connection

def create_test_entry():
    """Create a test entry with an overdue intended end date"""
    
    app = create_app()
    
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # First, ensure we have an entry type with show_end_dates enabled
            cursor.execute("""
                SELECT id FROM EntryType WHERE show_end_dates = 1 LIMIT 1
            """)
            entry_type = cursor.fetchone()
            
            if not entry_type:
                # Create a test entry type with end dates enabled
                cursor.execute("""
                    INSERT INTO EntryType 
                    (name, singular_label, plural_label, description, show_end_dates)
                    VALUES (?, ?, ?, ?, ?)
                """, ('test_project', 'Test Project', 'Test Projects', 
                      'A test project type for overdue notifications', 1))
                entry_type_id = cursor.lastrowid
                print(f"Created test entry type with ID: {entry_type_id}")
            else:
                entry_type_id = entry_type['id']
                print(f"Using existing entry type with ID: {entry_type_id}")
            
            # Create a test entry with an overdue intended end date
            # Set the intended end date to 3 days ago
            overdue_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO Entry 
                (title, description, entry_type_id, created_at, intended_end_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('Overdue Test Project', 
                  'A test project to demonstrate overdue notifications', 
                  entry_type_id, current_time, overdue_date, 'active'))
            
            entry_id = cursor.lastrowid
            conn.commit()
            
            print(f"Created test entry with ID: {entry_id}")
            print(f"Entry title: 'Overdue Test Project'")
            print(f"Intended end date: {overdue_date} (3 days ago)")
            print(f"Status: active")
            
            return entry_id
            
        except Exception as e:
            print(f"Error creating test entry: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def main():
    print("Creating test entry with overdue intended end date...")
    entry_id = create_test_entry()
    
    if entry_id:
        print(f"\nTest entry created successfully!")
        print("Now run the overdue checker to see it in action:")
        print("python check_overdue_dates.py")
        print("\nOr test the API endpoint:")
        print("curl -X POST http://localhost:5000/api/check_overdue_end_dates")
    else:
        print("Failed to create test entry.")

if __name__ == "__main__":
    main()
