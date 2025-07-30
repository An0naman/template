import sqlite3
from datetime import datetime
import os

def get_db_path():
    # Use local data directory for development
    db_dir = 'data'
    os.makedirs(db_dir, exist_ok=True) # Ensure the directory exists
    return os.path.join(db_dir, 'template.db')

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- EntryType Table ---
    # Defines the different types of entries (e.g., Batch, Ingredient, Recipe)
    # Includes labels for display and configurable note types
    # is_primary column is correctly included here
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EntryType (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,            -- Internal identifier (e.g., 'batch', 'ingredient')
            singular_label TEXT NOT NULL,         -- User-facing singular (e.g., 'Batch', 'Ingredient')
            plural_label TEXT NOT NULL,           -- User-facing plural (e.g., 'Batches', 'Ingredients')
            description TEXT,
            note_types TEXT DEFAULT 'General',    -- Comma-separated list of allowed note types for this EntryType
            is_primary BOOLEAN NOT NULL DEFAULT 0, -- This line is correct and should remain
            has_sensors BOOLEAN NOT NULL DEFAULT 0, -- Whether this entry type supports sensor data
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: Add has_sensors column if it doesn't exist
    try:
        cursor.execute("PRAGMA table_info(EntryType)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'has_sensors' not in columns:
            cursor.execute("ALTER TABLE EntryType ADD COLUMN has_sensors BOOLEAN NOT NULL DEFAULT 0")
    except Exception as e:
        # Column might already exist, ignore error
        pass

    # --- Entry Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            entry_type_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE RESTRICT
        )
    ''')

    # --- Basic Migration for Entry Table (if it already exists with old schema) ---
    # This migration logic is complex for init_db, but kept as per your existing file.
    try:
        cursor.execute("PRAGMA table_info(Entry)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'type' in columns and 'entry_type_id' not in columns:
            print("Detected old 'Entry' schema. Attempting migration steps.")
            cursor.execute("ALTER TABLE Entry ADD COLUMN entry_type_id INTEGER")
            print("Added 'entry_type_id' column to Entry table.")

            cursor.execute("INSERT OR IGNORE INTO EntryType (name, singular_label, plural_label, description, note_types) VALUES (?, ?, ?, ?, ?)",
                            ('general_entry', 'Entry', 'Entries', 'Default entry type for existing data', 'General'))
            conn.commit()

            cursor.execute("SELECT id FROM EntryType WHERE name = 'general_entry'")
            general_entry_type_id = cursor.fetchone()[0]

            cursor.execute("UPDATE Entry SET entry_type_id = ?", (general_entry_type_id,))
            print(f"Updated existing entries to use entry_type_id = {general_entry_type_id} ('general_entry').")

            cursor.execute("CREATE TABLE Entry_new (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, entry_type_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE RESTRICT)")
            cursor.execute("INSERT INTO Entry_new (id, title, description, entry_type_id, created_at) SELECT id, title, description, entry_type_id, created_at FROM Entry")
            cursor.execute("DROP TABLE Entry")
            cursor.execute("ALTER TABLE Entry_new RENAME TO Entry")
            print("Made 'entry_type_id' NOT NULL in Entry table.")
            print("Old 'type' column implicitly removed during table recreation.")

    except sqlite3.OperationalError as e:
        if "duplicate column name: entry_type_id" in str(e):
            print("Column 'entry_type_id' already exists in 'Entry' table. Skipping initial migration.")
        elif "no such column: entry_type_id" in str(e):
             print(f"Column 'entry_type_id' not found in Entry, but also not the 'type' column. Error: {e}")
        else:
            print(f"An unexpected error occurred during Entry table migration: {e}")

    try:
        cursor.execute("ALTER TABLE Entry ADD COLUMN description TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name: description" not in str(e):
            raise e

    # --- EntryRelationship Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EntryRelationship (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entry_id INTEGER NOT NULL,
            target_entry_id INTEGER NOT NULL,
            relationship_type TEXT NOT NULL,
            quantity TEXT,
            unit TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
            FOREIGN KEY (target_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
            UNIQUE(source_entry_id, target_entry_id, relationship_type)
        )
    ''')

    # --- RelationshipDefinition Table ---
    # This was the problematic one due to indentation.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RelationshipDefinition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,            -- Unique identifier for this relationship type (e.g., 'batch_ingredient_link')
            description TEXT,
            entry_type_id_from INTEGER NOT NULL,  -- FK to EntryType.id (the 'source' EntryType)
            entry_type_id_to INTEGER NOT NULL,    -- FK to EntryType.id (the 'target' EntryType)
            cardinality_from TEXT NOT NULL,       -- e.g., 'one', 'many'
            cardinality_to TEXT NOT NULL,         -- e.g., 'one', 'many'
            label_from_side TEXT NOT NULL,        -- Label when displaying from 'from' perspective (e.g., 'Ingredients')
            label_to_side TEXT NOT NULL,          -- Label when displaying from 'to' perspective (e.g., 'Used In Batches')
            allow_quantity_unit BOOLEAN NOT NULL DEFAULT 0, -- Does this relationship support quantity/unit?
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_type_id_from) REFERENCES EntryType(id) ON DELETE RESTRICT,
            FOREIGN KEY (entry_type_id_to) REFERENCES EntryType(id) ON DELETE RESTRICT
        )
    ''')

    # --- SensorData Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            sensor_type TEXT,
            value TEXT,
            recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
        )
    ''')

    # --- Note Table (FIXED: Reverted to entry_id to match app.py) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Note (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,            -- REVERTED: Now matches app.py's expectation
            note_title TEXT,
            note_text TEXT NOT NULL,
            type TEXT,                            -- Configurable note type (e.g., 'General', 'Fermentation Log')
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            image_paths TEXT DEFAULT '[]',        -- Added for future Immich integration
            FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
        )
    ''')
    # Basic migration for Note table columns (note_title, note_text, type, image_paths)
    for column, default_value in [('note_title', "''"), ('note_text', "''"), ('type', "'General'"), ('image_paths', "'[]'")]:
        try:
            cursor.execute(f"ALTER TABLE Note ADD COLUMN {column} TEXT DEFAULT {default_value}")
            print(f"Added '{column}' column to Note table.")
        except sqlite3.OperationalError as e:
            if f"duplicate column name: {column}" not in str(e):
                raise e

    # --- NotePhoto Table (still here, though image_paths is now in Note) ---
    # This table might become redundant if image_paths in Note is sufficient.
    # Keeping it as it was in your provided db.py
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NotePhoto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER,
            image_path TEXT, -- This will store Immich asset ID or URL
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (note_id) REFERENCES Note(id) ON DELETE CASCADE
        )
    ''')

    # --- SystemParameters Table (FIXED: Reverted to parameter_name and parameter_value) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SystemParameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter_name TEXT UNIQUE NOT NULL, -- REVERTED: Now matches app.py's expectation
            parameter_value TEXT,                -- REVERTED: Now matches app.py's expectation
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Initial System Parameters for Labels ---
    # Insert default values for entry labels if they don't exist
    # FIX: Changed 'key' to 'parameter_name' and 'value' to 'parameter_value'
    cursor.execute("INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) VALUES ('entry_singular_label', 'Entry')")
    cursor.execute("INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) VALUES ('entry_plural_label', 'Entries')")
    cursor.execute("INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) VALUES ('default_entry_type_name', 'general_entry')")
    cursor.execute("INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) VALUES ('project_name', 'My Awesome Project')") # Ensure project_name is also initialized

    # MaintenanceTask Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MaintenanceTask (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            task_name TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
            priority TEXT DEFAULT 'Medium' CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
        )
    ''')

    # MaintenanceLog Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MaintenanceLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            log_text TEXT NOT NULL,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES MaintenanceTask(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(get_db_path())