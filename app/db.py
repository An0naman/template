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
                has_sensors BOOLEAN NOT NULL DEFAULT 0, -- Whether this entry type supports sensor data
                enabled_sensor_types TEXT DEFAULT '', -- Comma-separated list of enabled sensor types for this entry type
                show_labels_section BOOLEAN NOT NULL DEFAULT 1, -- Whether to show the labels section for entries of this type
                show_end_dates BOOLEAN NOT NULL DEFAULT 0 -- Whether to show the end date fields (intended and actual) for entries of this type
            );
        ''')

        # Migration: Add has_sensors column if it doesn't exist
        try:
            cursor.execute("PRAGMA table_info(EntryType)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'has_sensors' not in columns:
                cursor.execute("ALTER TABLE EntryType ADD COLUMN has_sensors BOOLEAN NOT NULL DEFAULT 0")
            if 'enabled_sensor_types' not in columns:
                cursor.execute("ALTER TABLE EntryType ADD COLUMN enabled_sensor_types TEXT DEFAULT ''")
            if 'show_labels_section' not in columns:
                cursor.execute("ALTER TABLE EntryType ADD COLUMN show_labels_section BOOLEAN NOT NULL DEFAULT 1")
            if 'show_end_dates' not in columns:
                cursor.execute("ALTER TABLE EntryType ADD COLUMN show_end_dates BOOLEAN NOT NULL DEFAULT 0")
        except Exception as e:
            # Columns might already exist, ignore error
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
                file_paths TEXT DEFAULT '[]', -- JSON string of file paths
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

        # Migration: Add label printing columns to Entry table if they don't exist
        try:
            cursor.execute("PRAGMA table_info(Entry)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing label printing columns
            for column_name, column_def in [
                ('intended_end_date', 'TEXT'),
                ('actual_end_date', 'TEXT'),
                ('status', 'TEXT DEFAULT "active"')
            ]:
                if column_name not in columns:
                    cursor.execute(f'ALTER TABLE Entry ADD COLUMN {column_name} {column_def}')
                    logger.info(f"Added column '{column_name}' to Entry table")
        except Exception as e:
            logger.error(f"Error during Entry table migration: {e}")

        # Migration: Rename image_paths to file_paths in Note table
        try:
            cursor.execute("PRAGMA table_info(Note)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'image_paths' in columns and 'file_paths' not in columns:
                # SQLite doesn't support renaming columns directly, so we need to:
                # 1. Add the new column
                # 2. Copy data from old column to new column
                # 3. Drop the old column (requires recreating the table)
                
                # Step 1: Add file_paths column
                cursor.execute("ALTER TABLE Note ADD COLUMN file_paths TEXT DEFAULT '[]'")
                
                # Step 2: Copy data from image_paths to file_paths
                cursor.execute("UPDATE Note SET file_paths = image_paths WHERE image_paths IS NOT NULL")
                
                # Step 3: Create new table without image_paths and copy data
                cursor.execute('''
                    CREATE TABLE Note_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entry_id INTEGER NOT NULL,
                        note_title TEXT,
                        note_text TEXT NOT NULL,
                        type TEXT DEFAULT 'General',
                        created_at TEXT NOT NULL,
                        file_paths TEXT DEFAULT '[]',
                        FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
                    )
                ''')
                
                # Copy all data to new table
                cursor.execute('''
                    INSERT INTO Note_new (id, entry_id, note_title, note_text, type, created_at, file_paths)
                    SELECT id, entry_id, note_title, note_text, type, created_at, file_paths FROM Note
                ''')
                
                # Drop old table and rename new table
                cursor.execute("DROP TABLE Note")
                cursor.execute("ALTER TABLE Note_new RENAME TO Note")
                
                logger.info("Migrated Note table: renamed image_paths to file_paths")
            elif 'file_paths' not in columns:
                # Add file_paths column if it doesn't exist
                cursor.execute("ALTER TABLE Note ADD COLUMN file_paths TEXT DEFAULT '[]'")
                logger.info("Added file_paths column to Note table")
                
        except Exception as e:
            logger.error(f"Error during Note table migration: {e}")

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

        # Create SensorData Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SensorData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                sensor_type TEXT NOT NULL,
                value TEXT NOT NULL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
            );
        ''')

        # Create Notification Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Notification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL, -- 'note_based', 'sensor_based', 'manual'
                priority TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
                entry_id INTEGER, -- Related entry (optional)
                note_id INTEGER, -- Related note (optional for note-based notifications)
                scheduled_for TEXT, -- ISO datetime when notification should be shown
                is_read INTEGER DEFAULT 0, -- 0 for unread, 1 for read
                is_dismissed INTEGER DEFAULT 0, -- 0 for not dismissed, 1 for dismissed
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                read_at TEXT, -- When the notification was read
                dismissed_at TEXT, -- When the notification was dismissed
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (note_id) REFERENCES Note(id) ON DELETE CASCADE
            );
        ''')

        # Create NotificationRule Table for sensor-based notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS NotificationRule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                entry_type_id INTEGER, -- Optional: apply to specific entry type
                entry_id INTEGER, -- Optional: apply to specific entry
                sensor_type TEXT NOT NULL,
                condition_type TEXT NOT NULL, -- 'greater_than', 'less_than', 'equals', 'between', 'change_rate'
                threshold_value REAL, -- Primary threshold value
                threshold_value_secondary REAL, -- For 'between' conditions
                threshold_unit TEXT, -- Unit for the threshold
                is_active INTEGER DEFAULT 1, -- 0 for inactive, 1 for active
                notification_title TEXT NOT NULL,
                notification_message TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                cooldown_minutes INTEGER DEFAULT 60, -- Minimum minutes between notifications for same rule
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
            );
        ''')

        # Create Device Management Tables
        
        # Create RegisteredDevices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS RegisteredDevices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_name TEXT NOT NULL,
                ip TEXT NOT NULL,
                device_type TEXT NOT NULL,
                capabilities TEXT,
                status TEXT DEFAULT 'unknown',
                last_seen TIMESTAMP,
                polling_enabled BOOLEAN DEFAULT 1,
                polling_interval INTEGER DEFAULT 30,
                last_poll_success TIMESTAMP,
                last_poll_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add missing columns to RegisteredDevices if they don't exist
        try:
            cursor.execute('ALTER TABLE RegisteredDevices ADD COLUMN last_poll_success TIMESTAMP')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE RegisteredDevices ADD COLUMN last_poll_error TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create DeviceEntryLinks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DeviceEntryLinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                entry_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES RegisteredDevices (id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry (id) ON DELETE CASCADE,
                UNIQUE(device_id, entry_id)
            )
        ''')
        
        # Create DeviceSensorMapping table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DeviceSensorMapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                sensor_name TEXT NOT NULL,
                entry_field TEXT NOT NULL,
                data_type TEXT DEFAULT 'text',
                unit TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES RegisteredDevices (id) ON DELETE CASCADE,
                UNIQUE(device_id, sensor_name)
            )
        ''')

        # Insert default system parameters if they don't exist
        default_params = {
            # General settings
            'project_name': 'My Awesome Project',
            'entry_singular_label': 'Entry',
            'entry_plural_label': 'Entries',
            'sensor_types': 'Temperature,Humidity,Pressure,pH,Light,Motion,Sound,Vibration,Distance,Weight,Voltage,Current',
            'project_logo_path': '',
            
            # Label printing settings
            'label_font_size': '10',
            'label_include_qr_code': 'true',
            'label_include_logo': 'true',
            'label_qr_code_prefix': 'https://example.com',
            
            # Notification settings
            'overdue_check_enabled': 'true',
            'overdue_check_schedule': '0 9 * * *'  # Daily at 9:00 AM by default
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
                'entry_plural_label': 'Entries',
                'sensor_types': 'Temperature,Humidity,Pressure,pH,Light,Motion,Sound,Vibration,Distance,Weight,Voltage,Current',
                'allowed_file_types': 'txt,pdf,png,jpg,jpeg,gif,webp,svg,doc,docx,xls,xlsx,ppt,pptx,mp4,avi,mov,wmv,flv,webm,mkv,mp3,wav,flac,aac,ogg,zip,rar,7z,tar,gz',
                'max_file_size': '50',
                'custom_note_types': '[]'
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