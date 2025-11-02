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

        # Create EntryState Table for configurable status states
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryState (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('active', 'inactive')), -- Whether this state represents active or inactive
                color TEXT DEFAULT '#6c757d', -- Hex color for display
                display_order INTEGER DEFAULT 0, -- Order in which states should be displayed
                is_default INTEGER DEFAULT 0, -- 1 if this is the default state for new entries
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entry_type_id, name),
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
            );
        ''')

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
                associated_entry_ids TEXT DEFAULT '[]', -- JSON array of associated entry IDs
                url_bookmarks TEXT DEFAULT '[]', -- JSON array of objects with url and friendly_name
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

        # Create UserPreferences Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS UserPreferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_name TEXT NOT NULL,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(preference_name)
            );
        ''')

        # Create SavedSearch Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SavedSearch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                search_term TEXT DEFAULT '',
                type_filter TEXT DEFAULT '',
                status_filter TEXT DEFAULT '',
                specific_states TEXT DEFAULT '',
                date_range TEXT DEFAULT '',
                sort_by TEXT DEFAULT 'created_desc',
                content_display TEXT DEFAULT '',
                result_limit TEXT DEFAULT '50',
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Migration: Add is_default column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE SavedSearch ADD COLUMN is_default INTEGER DEFAULT 0")
            conn.commit()
            logger.info("Added is_default column to SavedSearch table")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create Dashboard Table for storing dashboard configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Dashboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_default INTEGER DEFAULT 0, -- Whether this is the default dashboard
                layout_config TEXT DEFAULT '{"cols": 12, "rowHeight": 100}', -- JSON grid layout configuration
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Create DashboardWidget Table for storing widgets on dashboards
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DashboardWidget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dashboard_id INTEGER NOT NULL,
                widget_type TEXT NOT NULL, -- 'list', 'pie_chart', 'line_chart', 'ai_summary', 'stat_card'
                title TEXT NOT NULL,
                position_x INTEGER DEFAULT 0,
                position_y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 4, -- Grid columns
                height INTEGER DEFAULT 2, -- Grid rows
                config TEXT DEFAULT '{}', -- JSON configuration for the widget
                data_source_type TEXT, -- 'saved_search', 'entry_states', 'sensor_data'
                data_source_id INTEGER, -- ID of the saved search or other data source
                refresh_interval INTEGER DEFAULT 300, -- Refresh interval in seconds (0 = manual only)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dashboard_id) REFERENCES Dashboard(id) ON DELETE CASCADE
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
                is_hierarchical INTEGER DEFAULT 0, -- 1 if parent-child relationship, 0 otherwise
                hierarchy_direction TEXT DEFAULT 'from_to_child', -- 'from_to_child' means FROM is parent, TO is child; 'to_from_child' means TO is parent, FROM is child
                is_active INTEGER DEFAULT 1, -- 1 for active, 0 for inactive
                FOREIGN KEY (entry_type_id_from) REFERENCES EntryType(id) ON DELETE RESTRICT,
                FOREIGN KEY (entry_type_id_to) REFERENCES EntryType(id) ON DELETE RESTRICT
            );
        ''')

        # Migration: Add is_hierarchical column to RelationshipDefinition if it doesn't exist
        try:
            cursor.execute("PRAGMA table_info(RelationshipDefinition)")
            rd_columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_hierarchical' not in rd_columns:
                cursor.execute('''
                    ALTER TABLE RelationshipDefinition
                    ADD COLUMN is_hierarchical INTEGER DEFAULT 0
                ''')
                logger.info("Added is_hierarchical column to RelationshipDefinition table")
            
            if 'hierarchy_direction' not in rd_columns:
                cursor.execute('''
                    ALTER TABLE RelationshipDefinition
                    ADD COLUMN hierarchy_direction TEXT DEFAULT 'from_to_child'
                ''')
                logger.info("Added hierarchy_direction column to RelationshipDefinition table")
        except Exception as e:
            logger.error(f"Error adding columns to RelationshipDefinition: {e}")
        
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
        
            # Migration for associated_entry_ids column
            cursor.execute("PRAGMA table_info(Note)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'associated_entry_ids' not in columns:
                # Add associated_entry_ids column if it doesn't exist
                cursor.execute("ALTER TABLE Note ADD COLUMN associated_entry_ids TEXT DEFAULT '[]'")
                logger.info("Added associated_entry_ids column to Note table")
            
            # Migration for url_bookmarks column
            cursor.execute("PRAGMA table_info(Note)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'url_bookmarks' not in columns:
                # Add url_bookmarks column if it doesn't exist
                cursor.execute("ALTER TABLE Note ADD COLUMN url_bookmarks TEXT DEFAULT '[]'")
                logger.info("Added url_bookmarks column to Note table")
                
                # If there's an existing 'urls' column, migrate data to the new format
                if 'urls' in columns:
                    cursor.execute("SELECT id, urls FROM Note WHERE urls IS NOT NULL AND urls != '[]'")
                    notes_with_urls = cursor.fetchall()
                    
                    for note in notes_with_urls:
                        try:
                            old_urls = json.loads(note['urls']) if note['urls'] else []
                            # Convert simple URL strings to the new format with friendly names
                            new_bookmarks = []
                            for url in old_urls:
                                if isinstance(url, str):
                                    # Extract domain name as friendly name
                                    from urllib.parse import urlparse
                                    parsed = urlparse(url)
                                    friendly_name = parsed.netloc or url
                                    new_bookmarks.append({
                                        'url': url,
                                        'friendly_name': friendly_name
                                    })
                                elif isinstance(url, dict) and 'url' in url:
                                    # Already in the correct format
                                    new_bookmarks.append({
                                        'url': url['url'],
                                        'friendly_name': url.get('friendly_name', url['url'])
                                    })
                            
                            # Update the note with the new format
                            cursor.execute(
                                "UPDATE Note SET url_bookmarks = ? WHERE id = ?",
                                (json.dumps(new_bookmarks), note['id'])
                            )
                        except (json.JSONDecodeError, Exception) as e:
                            logger.warning(f"Error migrating URLs for note {note['id']}: {e}")
                    
                    logger.info(f"Migrated URLs to url_bookmarks format for {len(notes_with_urls)} notes")
                
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

        # Create SensorData Table (legacy - for backward compatibility)
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

        # Create SharedSensorData Table (new efficient model)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SharedSensorData (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_type TEXT NOT NULL,
                value TEXT NOT NULL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                source_type TEXT DEFAULT 'manual', -- 'device', 'manual', 'api'
                source_id TEXT, -- device_id if from device, user_id if manual, etc.
                metadata TEXT DEFAULT '{}', -- JSON for additional sensor metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create range-based linking table for sensor data to entries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SensorDataEntryRanges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                sensor_type TEXT NOT NULL,
                start_sensor_id INTEGER NOT NULL, -- First sensor ID in range
                end_sensor_id INTEGER NOT NULL,   -- Last sensor ID in range (inclusive)
                link_type TEXT DEFAULT 'primary', -- 'primary', 'secondary', 'reference'
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}', -- JSON for additional range metadata
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                FOREIGN KEY (start_sensor_id) REFERENCES SharedSensorData(id) ON DELETE CASCADE,
                FOREIGN KEY (end_sensor_id) REFERENCES SharedSensorData(id) ON DELETE CASCADE,
                CHECK (end_sensor_id >= start_sensor_id) -- Ensure valid range
            );
        ''')
        
        # Keep the old SensorDataEntryLinks for backwards compatibility (will be migrated)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SensorDataEntryLinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shared_sensor_data_id INTEGER NOT NULL,
                entry_id INTEGER NOT NULL,
                link_type TEXT DEFAULT 'primary', -- 'primary', 'secondary', 'reference'
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shared_sensor_data_id) REFERENCES SharedSensorData(id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                UNIQUE(shared_sensor_data_id, entry_id) -- Prevent duplicate links
            );
        ''')
        
        # Create indexes for performance
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_shared_sensor_data_type_time ON SharedSensorData(sensor_type, recorded_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_entry_links_entry ON SensorDataEntryLinks(entry_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_entry_links_sensor ON SensorDataEntryLinks(shared_sensor_data_id)')
            # Range-based indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_entry ON SensorDataEntryRanges(entry_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_type ON SensorDataEntryRanges(sensor_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_start ON SensorDataEntryRanges(start_sensor_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_end ON SensorDataEntryRanges(end_sensor_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_entry_type ON SensorDataEntryRanges(entry_id, sensor_type)')
        except Exception as e:
            # Indexes might already exist, ignore errors
            pass

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
                auto_record BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES RegisteredDevices (id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry (id) ON DELETE CASCADE,
                UNIQUE(device_id, entry_id)
            )
        ''')
        
        # Add missing column to DeviceEntryLinks if it doesn't exist
        try:
            cursor.execute('ALTER TABLE DeviceEntryLinks ADD COLUMN auto_record BOOLEAN DEFAULT 1')
            logger.info("Added auto_record column to DeviceEntryLinks table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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

        # Create NoteBinding table for managing automatic note associations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS NoteBinding (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entry_id INTEGER NOT NULL, -- The entry where notes are created
                target_entry_id INTEGER NOT NULL, -- The entry to automatically associate notes with
                enabled BOOLEAN DEFAULT 1, -- Whether the binding is active
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_entry_id) REFERENCES Entry (id) ON DELETE CASCADE,
                FOREIGN KEY (target_entry_id) REFERENCES Entry (id) ON DELETE CASCADE,
                UNIQUE(source_entry_id, target_entry_id) -- Prevent duplicate bindings
            )
        ''')

        # Insert default system parameters if they don't exist
        default_params = {
            # General settings
            'project_name': 'My Awesome Project',
            'entry_singular_label': 'Entry',
            'entry_plural_label': 'Entries',
            'project_subtitle': 'Management System',  # Configurable subtitle
            'sensor_types': '',  # Start with empty sensor types - let devices register them dynamically
            'project_logo_path': '',
            
            # Label printing settings (defaults for all sizes)
            'label_font_size': '10',
            'label_title_font_size': '14',
            'label_include_qr_code': 'true',
            'label_include_logo': 'false',
            'label_logo_position': 'top-left',
            'label_qr_code_prefix': 'https://example.com',
            'label_border_style': 'simple',
            'label_text_wrap': 'true',
            'label_qr_size': 'medium',
            'label_qr_position': 'right',
            
            # Per-size label settings - 60x30mm (larger labels)
            'label_60x30mm_font_size': '8',
            'label_60x30mm_title_font_size': '12',
            'label_60x30mm_border_style': 'simple',
            'label_60x30mm_include_qr_code': 'true',
            'label_60x30mm_include_logo': 'false',
            'label_60x30mm_logo_position': 'top-left',
            'label_60x30mm_qr_size': 'medium',
            'label_60x30mm_qr_position': 'right',
            
            # Per-size label settings - 50x14mm (medium labels)
            'label_50x14mm_font_size': '7',
            'label_50x14mm_title_font_size': '10',
            'label_50x14mm_border_style': 'none',
            'label_50x14mm_include_qr_code': 'false',
            'label_50x14mm_qr_size': 'small',
            'label_50x14mm_qr_position': 'right',
            
            # Per-size label settings - 40x12mm (small labels)
            'label_40x12mm_font_size': '6',
            'label_40x12mm_title_font_size': '9',
            'label_40x12mm_border_style': 'none',
            'label_40x12mm_include_qr_code': 'false',
            'label_40x12mm_qr_size': 'small',
            'label_40x12mm_qr_position': 'right',
            
            # Per-size label settings - 30x15mm (narrow labels)
            'label_30x15mm_font_size': '7',
            'label_30x15mm_title_font_size': '10',
            'label_30x15mm_border_style': 'simple',
            'label_30x15mm_include_qr_code': 'true',
            'label_30x15mm_qr_size': 'small',
            'label_30x15mm_qr_position': 'bottom-right',
            
            # Per-size label settings - 30x12mm (B1 - small labels)
            'label_30x12mm_font_size': '6',
            'label_30x12mm_title_font_size': '9',
            'label_30x12mm_border_style': 'none',
            'label_30x12mm_include_qr_code': 'false',
            'label_30x12mm_qr_size': 'small',
            'label_30x12mm_qr_position': 'right',
            
            # Per-size label settings - 40x20mm (B1 - medium labels)
            'label_40x20mm_font_size': '7',
            'label_40x20mm_title_font_size': '10',
            'label_40x20mm_border_style': 'simple',
            'label_40x20mm_include_qr_code': 'true',
            'label_40x20mm_qr_size': 'small',
            'label_40x20mm_qr_position': 'right',
            
            # Per-size label settings - 40x24mm (B1 - medium-large labels)
            'label_40x24mm_font_size': '8',
            'label_40x24mm_title_font_size': '11',
            'label_40x24mm_border_style': 'simple',
            'label_40x24mm_include_qr_code': 'true',
            'label_40x24mm_qr_size': 'medium',
            'label_40x24mm_qr_position': 'right',
            
            # Per-size label settings - 75x12mm (D110 - wide labels)
            'label_75x12mm_font_size': '7',
            'label_75x12mm_title_font_size': '10',
            'label_75x12mm_border_style': 'none',
            'label_75x12mm_include_qr_code': 'false',
            'label_75x12mm_qr_size': 'small',
            'label_75x12mm_qr_position': 'right',
            
            # Rotated label settings (90 degrees) - for landscape orientation
            # 60x30mm rotated becomes 30x60mm (landscape)
            'label_60x30mm_r90_font_size': '10',
            'label_60x30mm_r90_title_font_size': '14',
            'label_60x30mm_r90_border_style': 'simple',
            'label_60x30mm_r90_include_qr_code': 'true',
            'label_60x30mm_r90_qr_size': 'large',
            'label_60x30mm_r90_qr_position': 'top-right',
            
            # 50x14mm rotated (landscape)
            'label_50x14mm_r90_font_size': '7',
            'label_50x14mm_r90_title_font_size': '10',
            'label_50x14mm_r90_border_style': 'simple',
            'label_50x14mm_r90_include_qr_code': 'true',
            'label_50x14mm_r90_qr_size': 'small',
            'label_50x14mm_r90_qr_position': 'top-right',
            
            # 40x12mm rotated (landscape)
            'label_40x12mm_r90_font_size': '6',
            'label_40x12mm_r90_title_font_size': '9',
            'label_40x12mm_r90_border_style': 'simple',
            'label_40x12mm_r90_include_qr_code': 'true',
            'label_40x12mm_r90_qr_size': 'small',
            'label_40x12mm_r90_qr_position': 'top-right',
            
            # 30x15mm rotated (landscape)
            'label_30x15mm_r90_font_size': '7',
            'label_30x15mm_r90_title_font_size': '10',
            'label_30x15mm_r90_border_style': 'simple',
            'label_30x15mm_r90_include_qr_code': 'true',
            'label_30x15mm_r90_qr_size': 'small',
            'label_30x15mm_r90_qr_position': 'top-right',
            
            # Notification settings
            'overdue_check_enabled': 'true',
            'overdue_check_schedule': '0 9 * * *',  # Daily at 9:00 AM by default
            
            # Default search parameters for index page
            'default_search_term': '',
            'default_type_filter': '',
            'default_status_filter': '',
            'default_date_range': '',
            'default_sort_by': 'created_desc',
            'default_content_display': '',
            'default_result_limit': '50'
        }
        for name, value in default_params.items():
            cursor.execute("INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", (name, value))

        # Migration: Add default states for all entry types that don't have any states yet
        try:
            cursor.execute("SELECT id FROM EntryType")
            entry_types = cursor.fetchall()
            
            for entry_type_row in entry_types:
                entry_type_id = entry_type_row[0]
                
                # Check if this entry type already has states
                cursor.execute("SELECT COUNT(*) FROM EntryState WHERE entry_type_id = ?", (entry_type_id,))
                state_count = cursor.fetchone()[0]
                
                if state_count == 0:
                    # Add default active and inactive states
                    cursor.execute('''
                        INSERT INTO EntryState (entry_type_id, name, category, color, display_order, is_default)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (entry_type_id, 'Active', 'active', '#28a745', 0, 1))
                    
                    cursor.execute('''
                        INSERT INTO EntryState (entry_type_id, name, category, color, display_order, is_default)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (entry_type_id, 'Inactive', 'inactive', '#6c757d', 1, 0))
                    
                    logger.info(f"Added default states for entry type ID {entry_type_id}")
        except Exception as e:
            logger.error(f"Error during EntryState migration: {e}")

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
                'sensor_types': '',  # Start with empty sensor types - let devices register them dynamically
                'allowed_file_types': 'txt,pdf,png,jpg,jpeg,gif,webp,svg,doc,docx,xls,xlsx,ppt,pptx,mp4,avi,mov,wmv,flv,webm,mkv,mp3,wav,flac,aac,ogg,zip,rar,7z,tar,gz',
                'max_file_size': '50',
                'custom_note_types': '[]',
                'gemini_api_key': '',  # Google Gemini API key for AI features
                'gemini_model_name': 'gemini-1.5-flash',  # Google Gemini model name
                'gemini_base_prompt': 'You are a helpful assistant for a project management application. Please provide clear, concise, and well-structured responses.'  # Base prompt for AI context
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

def get_user_preference(preference_name, default_value=None):
    """Get a user preference value by name"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT preference_value FROM UserPreferences WHERE preference_name = ?",
                (preference_name,)
            )
            result = cursor.fetchone()
            return result['preference_value'] if result else default_value
    except sqlite3.Error as e:
        logger.error(f"Error getting user preference {preference_name}: {e}")
        return default_value

def set_user_preference(preference_name, preference_value):
    """Set a user preference value (insert or update)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO UserPreferences (preference_name, preference_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(preference_name) DO UPDATE SET
                    preference_value = excluded.preference_value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (preference_name, preference_value))
            conn.commit()
            logger.debug(f"Set user preference {preference_name} = {preference_value}")
            return True
    except sqlite3.Error as e:
        logger.error(f"Error setting user preference {preference_name}: {e}")
        return False

def get_all_user_preferences():
    """Get all user preferences as a dictionary"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT preference_name, preference_value FROM UserPreferences")
            return {row['preference_name']: row['preference_value'] for row in cursor.fetchall()}
    except sqlite3.Error as e:
        logger.error(f"Error getting all user preferences: {e}")
        return {}