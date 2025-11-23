#!/usr/bin/env python3
"""
Migration: Add SensorLogs table for serial monitoring
=====================================================

Created: 2025-11-23
Description: Creates table to store serial output/logs from ESP32 sensors
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database path"""
    if os.path.exists('/app/data'):
        return '/app/data/template.db'
    
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / 'template.db')

def migration_already_applied(cursor):
    """Check if migration has already been applied"""
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SensorLogs'
        """)
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return False

def apply_migration(conn, cursor):
    """Apply the migration"""
    try:
        logger.info("Creating SensorLogs table...")
        
        cursor.execute("""
            CREATE TABLE SensorLogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                log_level TEXT DEFAULT 'INFO',
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
            )
        """)
        
        logger.info("Creating indexes...")
        
        # Index on sensor_id for quick lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_logs_sensor_id 
            ON SensorLogs(sensor_id)
        """)
        
        # Index on timestamp for time-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_logs_timestamp 
            ON SensorLogs(timestamp DESC)
        """)
        
        # Composite index for sensor + time
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_logs_sensor_time 
            ON SensorLogs(sensor_id, timestamp DESC)
        """)
        
        conn.commit()
        logger.info("✓ Migration applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        conn.rollback()
        return False

def main():
    db_path = get_db_path()
    logger.info(f"Connecting to database: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        if migration_already_applied(cursor):
            logger.info("Migration add_sensor_logs.py already applied, skipping...")
            return 0
        
        if apply_migration(conn, cursor):
            logger.info("Migration completed successfully!")
            return 0
        else:
            logger.error("Migration failed")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main())
