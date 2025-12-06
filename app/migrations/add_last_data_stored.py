import sqlite3
import os
import sys

DATABASE_PATH = os.environ.get('DATABASE_PATH', './data/template.db')

def migrate():
    print(f"Running migration: Add last_data_stored to RegisteredDevices")
    
    if not os.path.exists(DATABASE_PATH):
        # Try absolute path if relative fails
        DATABASE_PATH_ABS = '/home/an0naman/Documents/GitHub/template/data/template.db'
        if os.path.exists(DATABASE_PATH_ABS):
            db_path = DATABASE_PATH_ABS
        else:
            print(f"Database not found at {DATABASE_PATH}")
            return
    else:
        db_path = DATABASE_PATH
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(RegisteredDevices)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'last_data_stored' in columns:
            print("last_data_stored column already exists")
        else:
            print("Adding last_data_stored column...")
            cursor.execute("ALTER TABLE RegisteredDevices ADD COLUMN last_data_stored TIMESTAMP")
            conn.commit()
            print("Column added successfully")
            
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
