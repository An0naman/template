#!/usr/bin/env python3
"""
Migration: Implement shared sensor data model
- Creates new SharedSensorData table for storing sensor readings once
- Creates SensorDataEntryLinks table to link sensor data to multiple entries
- Migrates existing data from SensorData to new structure
- Provides rollback functionality
"""

import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_to_shared_sensor_data(db_path):
    """
    Migrate from single-entry sensor data to shared sensor data model
    
    New structure:
    - SharedSensorData: stores the actual sensor readings (sensor_type, value, recorded_at)
    - SensorDataEntryLinks: links sensor data to one or more entries
    """
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Create new SharedSensorData table
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
        
        # Create linking table for sensor data to entries
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_shared_sensor_data_type_time ON SharedSensorData(sensor_type, recorded_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_entry_links_entry ON SensorDataEntryLinks(entry_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_entry_links_sensor ON SensorDataEntryLinks(shared_sensor_data_id)')
        
        # Check if we need to migrate existing data
        cursor.execute('SELECT COUNT(*) FROM SensorData')
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"Migrating {existing_count} existing sensor data records...")
            
            # Migrate existing sensor data
            cursor.execute('SELECT * FROM SensorData ORDER BY recorded_at')
            old_sensor_data = cursor.fetchall()
            
            migration_map = {}  # Map old_id -> new_shared_id
            
            for old_record in old_sensor_data:
                # Insert into SharedSensorData
                cursor.execute('''
                    INSERT INTO SharedSensorData (sensor_type, value, recorded_at, source_type, metadata)
                    VALUES (?, ?, ?, 'migrated', ?)
                ''', (
                    old_record['sensor_type'],
                    old_record['value'], 
                    old_record['recorded_at'],
                    json.dumps({'migrated_from_sensor_data_id': old_record['id']})
                ))
                
                new_shared_id = cursor.lastrowid
                migration_map[old_record['id']] = new_shared_id
                
                # Create entry link
                cursor.execute('''
                    INSERT INTO SensorDataEntryLinks (shared_sensor_data_id, entry_id, link_type)
                    VALUES (?, ?, 'primary')
                ''', (new_shared_id, old_record['entry_id']))
            
            logger.info(f"Migration completed. Created {len(migration_map)} shared sensor records.")
            
            # Rename old table for backup
            cursor.execute('ALTER TABLE SensorData RENAME TO SensorData_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
            logger.info("Original SensorData table backed up")
        
        conn.commit()
        logger.info("Shared sensor data migration completed successfully")
        
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

def rollback_shared_sensor_data(db_path):
    """
    Rollback the shared sensor data migration
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find backup table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'SensorData_backup_%'")
        backup_tables = cursor.fetchall()
        
        if not backup_tables:
            logger.error("No backup table found for rollback")
            return False
        
        # Use the most recent backup
        backup_table = backup_tables[-1][0]
        logger.info(f"Rolling back from {backup_table}")
        
        # Restore original table
        cursor.execute(f'ALTER TABLE {backup_table} RENAME TO SensorData')
        
        # Drop new tables
        cursor.execute('DROP TABLE IF EXISTS SensorDataEntryLinks')
        cursor.execute('DROP TABLE IF EXISTS SharedSensorData')
        
        conn.commit()
        logger.info("Rollback completed successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Rollback failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python add_shared_sensor_data.py <database_path> [rollback]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == 'rollback':
        rollback_shared_sensor_data(db_path)
    else:
        migrate_to_shared_sensor_data(db_path)
