
import sqlite3
import sys
import os

# Add parent directory to path to import db module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

MIGRATION_NAME = 'migrate_scripts_to_library.py'

def migrate_scripts():
    db_path = os.environ.get('DATABASE_PATH', './data/template.db')
    print(f"Connecting to database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if migration tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        if not cursor.fetchone():
            # Create it if it doesn't exist (it should, but just in case)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Check if this migration has already run
        cursor.execute("SELECT id FROM schema_migrations WHERE migration_name = ?", (MIGRATION_NAME,))
        if cursor.fetchone():
            print(f"Migration {MIGRATION_NAME} already applied. Skipping.")
            return

        # Check if ScriptLibrary exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ScriptLibrary'")
        if not cursor.fetchone():
            print("Error: ScriptLibrary table does not exist. Run the previous migration first.")
            return

        # Check if SensorScripts exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SensorScripts'")
        if not cursor.fetchone():
             print("SensorScripts table does not exist. Nothing to migrate.")
             # Mark as applied so we don't check again
             cursor.execute("INSERT INTO schema_migrations (migration_name) VALUES (?)", (MIGRATION_NAME,))
             conn.commit()
             return

        # Check if ScriptLibrary already has entries
        # If it does, we assume the migration has already run or the library is being used.
        # This prevents re-populating deleted scripts if the migration tracking wasn't previously in place.
        cursor.execute("SELECT count(*) FROM ScriptLibrary")
        if cursor.fetchone()[0] > 0:
             print("ScriptLibrary already has entries. Assuming migration already done.")
             cursor.execute("INSERT INTO schema_migrations (migration_name) VALUES (?)", (MIGRATION_NAME,))
             conn.commit()
             return

        # Get existing scripts from SensorScripts
        print("Fetching existing scripts from SensorScripts...")
        cursor.execute("SELECT * FROM SensorScripts")
        existing_scripts = cursor.fetchall()
        
        count = 0
        for script in existing_scripts:
            # Check if this script content already exists in library to avoid duplicates
            # We'll use a simple check on content and type
            cursor.execute(
                "SELECT id FROM ScriptLibrary WHERE script_content = ? AND script_type = ?", 
                (script['script_content'], script['script_type'])
            )
            if cursor.fetchone():
                print(f"Skipping duplicate script (ID: {script['id']})")
                continue
                
            # Create a name for the script
            # If description exists, use it, otherwise use "Imported Script {id}"
            name = script['description'] if script['description'] else f"Imported Script {script['id']}"
            if len(name) > 50:
                name = name[:47] + "..."
                
            # Insert into ScriptLibrary
            cursor.execute('''
                INSERT INTO ScriptLibrary 
                (name, script_content, script_version, script_type, description, target_sensor_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                name,
                script['script_content'],
                script['script_version'],
                script['script_type'],
                script['description'],
                None # We don't know the target type generally, or could infer from sensor_id but let's leave blank
            ))
            count += 1
            
        # Record migration as applied
        cursor.execute("INSERT INTO schema_migrations (migration_name) VALUES (?)", (MIGRATION_NAME,))
        
        conn.commit()
        print(f"Successfully migrated {count} scripts to ScriptLibrary.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_scripts()
