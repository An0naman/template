import sqlite3

def migrate():
    conn = sqlite3.connect('data/template.db')
    c = conn.cursor()
    
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(sensor_data)")
        columns = [info[1] for info in c.fetchall()]
        
        if 'battery_level' not in columns:
            print("Adding battery_level column to sensor_data table...")
            c.execute("ALTER TABLE sensor_data ADD COLUMN battery_level REAL")
            conn.commit()
            print("Migration successful!")
        else:
            print("Column battery_level already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
