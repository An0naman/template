
import sqlite3
import sys
import os

# Add parent directory to path to import db module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def migrate_scripts():
    db_path = os.environ.get('DATABASE_PATH', './data/template.db')
    print(f"Connecting to database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if ScriptLibrary exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ScriptLibrary'")
        if not cursor.fetchone():
            print("Error: ScriptLibrary table does not exist. Run the previous migration first.")
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
            
        conn.commit()
        print(f"Successfully migrated {count} scripts to ScriptLibrary.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_scripts()
