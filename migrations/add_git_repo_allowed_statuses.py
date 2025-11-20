"""
Add allowed_statuses column to GitRepository table
"""
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path to import db module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'template.db')
    if not os.path.exists(db_path):
        raise Exception(f"Database not found at {db_path}")
    return sqlite3.connect(db_path)

def migrate():
    """Add allowed_statuses column to GitRepository"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(GitRepository)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'allowed_statuses' not in columns:
            cursor.execute('''
                ALTER TABLE GitRepository 
                ADD COLUMN allowed_statuses TEXT
            ''')
            print("✓ Added allowed_statuses column to GitRepository table")
        else:
            print("✓ allowed_statuses column already exists, skipping...")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def rollback():
    """Rollback migration - remove allowed_statuses column"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support dropping columns easily, so we'd need to recreate the table
        # For now, just log that rollback isn't supported
        print("⚠️ Rollback not supported for this migration (SQLite limitation)")
        print("   Column 'allowed_statuses' will remain in table")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
