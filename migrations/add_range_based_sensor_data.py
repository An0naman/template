#!/usr/bin/env python3
"""
Migration: Implement range-based shared sensor data model
- Creates SensorDataEntryRanges table for efficient sensor data sharing using ranges
- Maps entry IDs to sensor ID ranges instead of individual links
- Much more efficient for continuous sensor data streams
"""

import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_to_range_based_sensor_data(db_path):
    """
    Migrate to range-based sensor data sharing model
    
    New structure:
    - SensorDataEntryRanges: maps entries to sensor ID ranges
    - Much more efficient than individual links
    """
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Create range-based linking table
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
        
        # Create indexes for efficient range queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_entry ON SensorDataEntryRanges(entry_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_type ON SensorDataEntryRanges(sensor_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_start ON SensorDataEntryRanges(start_sensor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_end ON SensorDataEntryRanges(end_sensor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_ranges_entry_type ON SensorDataEntryRanges(entry_id, sensor_type)')
        
        # Create function table for efficient range operations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SensorDataRangeFunctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT UNIQUE NOT NULL,
                description TEXT,
                sql_template TEXT NOT NULL, -- SQL template for range operations
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Insert predefined range functions
        range_functions = [
            {
                'function_name': 'get_sensor_data_for_entry_range',
                'description': 'Get all sensor data for an entry using ranges',
                'sql_template': '''
                    SELECT ssd.* FROM SharedSensorData ssd
                    JOIN SensorDataEntryRanges sder ON ssd.id BETWEEN sder.start_sensor_id AND sder.end_sensor_id
                    WHERE sder.entry_id = ? AND sder.sensor_type = ssd.sensor_type
                    ORDER BY ssd.recorded_at DESC
                '''
            },
            {
                'function_name': 'get_range_summary_for_entry',
                'description': 'Get range summary statistics for an entry',
                'sql_template': '''
                    SELECT 
                        sder.sensor_type,
                        COUNT(*) as range_count,
                        MIN(sder.start_sensor_id) as earliest_sensor_id,
                        MAX(sder.end_sensor_id) as latest_sensor_id,
                        SUM(sder.end_sensor_id - sder.start_sensor_id + 1) as total_readings_in_ranges
                    FROM SensorDataEntryRanges sder
                    WHERE sder.entry_id = ?
                    GROUP BY sder.sensor_type
                '''
            }
        ]
        
        for func in range_functions:
            cursor.execute('''
                INSERT OR REPLACE INTO SensorDataRangeFunctions 
                (function_name, description, sql_template) 
                VALUES (?, ?, ?)
            ''', (func['function_name'], func['description'], func['sql_template']))
        
        # Migrate existing SensorDataEntryLinks to ranges
        cursor.execute('SELECT COUNT(*) FROM SensorDataEntryLinks')
        existing_links = cursor.fetchone()[0]
        
        if existing_links > 0:
            logger.info(f"Converting {existing_links} individual links to ranges...")
            
            # Group consecutive sensor IDs by entry and sensor type
            cursor.execute('''
                SELECT 
                    sel.entry_id,
                    ssd.sensor_type,
                    sel.link_type,
                    GROUP_CONCAT(ssd.id ORDER BY ssd.id) as sensor_ids
                FROM SensorDataEntryLinks sel
                JOIN SharedSensorData ssd ON sel.shared_sensor_data_id = ssd.id
                GROUP BY sel.entry_id, ssd.sensor_type, sel.link_type
                ORDER BY sel.entry_id, ssd.sensor_type
            ''')
            
            link_groups = cursor.fetchall()
            ranges_created = 0
            
            for group in link_groups:
                entry_id = group['entry_id']
                sensor_type = group['sensor_type']
                link_type = group['link_type']
                sensor_ids = [int(sid) for sid in group['sensor_ids'].split(',')]
                
                # Create ranges from consecutive IDs
                ranges = create_ranges_from_ids(sensor_ids)
                
                for start_id, end_id in ranges:
                    cursor.execute('''
                        INSERT INTO SensorDataEntryRanges 
                        (entry_id, sensor_type, start_sensor_id, end_sensor_id, link_type, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        entry_id, sensor_type, start_id, end_id, link_type,
                        json.dumps({'migrated_from_links': True, 'original_link_count': len(sensor_ids)})
                    ))
                    ranges_created += 1
            
            logger.info(f"Created {ranges_created} ranges from {existing_links} individual links")
            
            # Backup and remove old links table
            cursor.execute('ALTER TABLE SensorDataEntryLinks RENAME TO SensorDataEntryLinks_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
            logger.info("Original SensorDataEntryLinks table backed up")
        
        conn.commit()
        logger.info("Range-based sensor data migration completed successfully")
        
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Range migration failed: {e}")
        raise
    finally:
        conn.close()

def create_ranges_from_ids(sensor_ids):
    """
    Create ranges from a list of sensor IDs
    Groups consecutive IDs into ranges for efficiency
    
    Args:
        sensor_ids: List of sensor IDs (should be sorted)
    
    Returns:
        List of (start_id, end_id) tuples
    """
    if not sensor_ids:
        return []
    
    sensor_ids = sorted(set(sensor_ids))  # Remove duplicates and sort
    ranges = []
    start = sensor_ids[0]
    end = sensor_ids[0]
    
    for i in range(1, len(sensor_ids)):
        if sensor_ids[i] == end + 1:
            # Consecutive ID, extend current range
            end = sensor_ids[i]
        else:
            # Gap found, close current range and start new one
            ranges.append((start, end))
            start = end = sensor_ids[i]
    
    # Add the final range
    ranges.append((start, end))
    
    return ranges

def rollback_range_based_sensor_data(db_path):
    """
    Rollback the range-based sensor data migration
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find backup table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'SensorDataEntryLinks_backup_%'")
        backup_tables = cursor.fetchall()
        
        if backup_tables:
            # Use the most recent backup
            backup_table = backup_tables[-1][0]
            logger.info(f"Rolling back from {backup_table}")
            
            # Restore original table
            cursor.execute(f'ALTER TABLE {backup_table} RENAME TO SensorDataEntryLinks')
        
        # Drop new tables
        cursor.execute('DROP TABLE IF EXISTS SensorDataEntryRanges')
        cursor.execute('DROP TABLE IF EXISTS SensorDataRangeFunctions')
        
        conn.commit()
        logger.info("Range-based rollback completed successfully")
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
        print("Usage: python add_range_based_sensor_data.py <database_path> [rollback]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == 'rollback':
        rollback_range_based_sensor_data(db_path)
    else:
        migrate_to_range_based_sensor_data(db_path)
