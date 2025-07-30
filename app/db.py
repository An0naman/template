# template_app/app/db.py
import sqlite3
from flask import current_app, g
import os
import json
import logging
from datetime import datetime

# Get the logger for this module
logger = logging.getLogger(__name__)

def get_connection():
    db_path = current_app.config['DATABASE_PATH']
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # Return rows as dict-like objects
        logger.debug(f"Connected to database: {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database at {db_path}: {e}")
        raise

def init_db():
    # This function is now called from run.py (or create_app in __init__.py for testing)
    # It ensures the database schema is set up.
    db_path = current_app.config['DATABASE_PATH']
    db_exists = os.path.exists(db_path)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Create EntryType Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryType (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                singular_label TEXT NOT NULL,
                plural_label TEXT NOT NULL,
                description TEXT,
                note_types TEXT DEFAULT 'General', -- Comma-separated list of default note types
                is_primary INTEGER DEFAULT 0, -- 1 for primary, 0 for secondary
                has_sensors BOOLEAN NOT NULL DEFAULT 0 -- Whether this entry type supports sensor data
            );
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

        # Create Entry Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                entry_type_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE RESTRICT
            );
        ''')

        # Create Note Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Note (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                note_title TEXT,
                note_text TEXT NOT NULL,
                type TEXT DEFAULT 'General',
                created_at TEXT NOT NULL,
                image_paths TEXT DEFAULT '[]', -- JSON string of image paths
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
            );
        ''')

        # Create SystemParameters Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SystemParameters (
                parameter_name TEXT PRIMARY KEY NOT NULL,
                parameter_value TEXT
            );
        ''')

        # Create RelationshipDefinition Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS RelationshipDefinition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                entry_type_id_from INTEGER NOT NULL,
                entry_type_id_to INTEGER NOT NULL,
                cardinality_from TEXT NOT NULL, -- e.g., "one", "many"
                cardinality_to TEXT NOT NULL,   -- e.g., "one", "many"
                label_from_side TEXT NOT NULL,  -- e.g., "parent of", "part of"
                label_to_side TEXT NOT NULL,    -- e.g., "child of", "has part"
                allow_quantity_unit INTEGER DEFAULT 0, -- 1 for true, 0 for false
                is_active INTEGER DEFAULT 1, -- 1 for active, 0 for inactive
                FOREIGN KEY (entry_type_id_from) REFERENCES EntryType(id) ON DELETE RESTRICT,
                FOREIGN KEY (entry_type_id_to) REFERENCES EntryType(id) ON DELETE RESTRICT
            );
        ''')

        # Create EntryRelationship Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryRelationship (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entry_id INTEGER NOT NULL, -- The entry from which the relationship originates
                target_entry_id INTEGER NOT NULL, -- The entry to which the relationship points
                relationship_type INTEGER NOT NULL, -- References RelationshipDefinition.id
                quantity REAL, -- For numerical quantities
                unit TEXT,     -- For units associated with quantity
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_entry_id, target_entry_id, relationship_type), -- Prevent duplicate relationships
                FOREIGN KEY (source_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (target_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (relationship_type) REFERENCES RelationshipDefinition(id) ON DELETE RESTRICT
            );
        ''')

        # Insert default system parameters if they don't exist
        default_params = {
            'project_name': 'My Awesome Project',
            'entry_singular_label': 'Entry',
            'entry_plural_label': 'Entries'
        }
        for name, value in default_params.items():
            cursor.execute("INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", (name, value))

        conn.commit()
        if not db_exists:
            logger.info("Database schema initialized and default system parameters inserted.")
        else:
            logger.info("Database schema checked and updated (if necessary), default system parameters ensured.")

def get_system_parameters():
    """
    Retrieves system parameters from the database.
    If no parameters exist, it initializes default ones.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters")
        params_list = cursor.fetchall()

        params = {}
        for row in params_list:
            params[row['parameter_name']] = row['parameter_value']

        # If after fetching, params is still empty, it means the table was empty or not properly initialized
        # This block now primarily ensures initial defaults if init_db didn't catch them, or for robustness.
        if not params:
            logger.info("SystemParameters table empty or not fully initialized, ensuring defaults.")
            default_params = {
                'project_name': 'My Awesome Project',
                'entry_singular_label': 'Entry',
                'entry_plural_label': 'Entries'
            }
            for name, value in default_params.items():
                try:
                    cursor.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", (name, value))
                    conn.commit()
                    params[name] = value # Add to current params dict
                except sqlite3.IntegrityError:
                    # This can happen if another process just inserted it
                    logger.warning(f"System parameter '{name}' already exists during default initialization attempt in get_system_parameters.")
                    # Re-fetch just this parameter in case it was created
                    cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (name,))
                    fetched_value = cursor.fetchone()
                    if fetched_value:
                        params[name] = fetched_value['parameter_value']
                    conn.rollback() # Rollback any failed insert attempt
                except Exception as e:
                    logger.error(f"Error initializing system parameter {name}: {e}", exc_info=True)
                    conn.rollback()
            # After potential inserts, re-fetch all to ensure consistency if new parameters were added
            cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters")
            params_list_re = cursor.fetchall()
            params = {row['parameter_name']: row['parameter_value'] for row in params_list_re}

        return params
    except Exception as e:
        logger.error(f"Critical error in get_system_parameters: {e}", exc_info=True)
        # In a critical error scenario, return a hardcoded default to allow app to function minimally
        return {
            'project_name': 'Error Loading Project Name',
            'entry_singular_label': 'Error Entry',
            'entry_plural_label': 'Error Entries'
        }
    finally:
        if conn and 'db' not in g: # Only close if not part of a request context
            conn.close()