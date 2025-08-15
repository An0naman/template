#!/usr/bin/env python3
"""
Migration to add ntfy_sent column to Notification table
"""

import sqlite3
import sys
import os

# Add the parent directory to the path to import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_connection

def migrate():
    """Add ntfy_sent column to Notification table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(Notification)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ntfy_sent' not in columns:
            print("Adding ntfy_sent column to Notification table...")
            cursor.execute('''
                ALTER TABLE Notification 
                ADD COLUMN ntfy_sent INTEGER DEFAULT 0
            ''')
            
            conn.commit()
            print("Successfully added ntfy_sent column to Notification table")
        else:
            print("ntfy_sent column already exists in Notification table")
        
        conn.close()
        
    except Exception as e:
        print(f"Error adding ntfy_sent column: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
