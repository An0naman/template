#!/usr/bin/env python3
"""
Migration: Fix SensorRegistration Foreign Key Constraint
========================================================

Created: 2025-11-23

Description: Removes the foreign key constraint on current_script_id in 
             SensorRegistration table that was causing issues when sensors
             reported their running script version.

Usage:
------
This migration will be automatically run by docker-entrypoint.sh on container startup.
You can also run it manually:
    python app/migrations/fix_sensor_registration_foreign_key.py
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get database path from environment or use default
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')


def migration_already_applied(cursor) -> bool:
    """Check if this migration has already been applied."""
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM schema_migrations 
            WHERE migration_name = ?
        """, (Path(__file__).name,))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return False
        raise


def apply_migration(cursor):
    """Apply the actual migration changes."""
    
    logger.info("Fixing SensorRegistration foreign key constraint...")
    
    # SQLite doesn't support DROP CONSTRAINT, so we need to recreate the table
    
    # 1. Create backup of data
    logger.info("Backing up SensorRegistration data...")
    cursor.execute('''
        CREATE TEMPORARY TABLE sensor_registration_backup AS
        SELECT * FROM SensorRegistration
    ''')
    
    # 2. Drop the old table
    logger.info("Dropping old SensorRegistration table...")
    cursor.execute('DROP TABLE IF EXISTS SensorRegistration')
    
    # 3. Recreate without foreign key constraint
    logger.info("Creating new SensorRegistration table without foreign key...")
    cursor.execute('''
        CREATE TABLE SensorRegistration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL UNIQUE,
            sensor_name TEXT,
            sensor_type TEXT NOT NULL,
            hardware_info TEXT,
            firmware_version TEXT,
            config_hash TEXT,
            current_script_id INTEGER,
            current_script_version TEXT,
            last_check_in TIMESTAMP,
            last_config_update TIMESTAMP,
            status TEXT DEFAULT 'pending',
            ip_address TEXT,
            mac_address TEXT,
            capabilities TEXT,
            registration_source TEXT DEFAULT 'auto',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Restore data (explicitly list columns to handle schema differences)
    logger.info("Restoring data...")
    cursor.execute('''
        INSERT INTO SensorRegistration (
            id, sensor_id, sensor_name, sensor_type, hardware_info, 
            firmware_version, config_hash, current_script_id, current_script_version,
            last_check_in, last_config_update, status, ip_address, 
            mac_address, capabilities, registration_source, created_at, updated_at
        )
        SELECT 
            id, sensor_id, sensor_name, sensor_type, hardware_info, 
            firmware_version, config_hash, current_script_id, current_script_version,
            last_check_in, last_config_update, status, ip_address, 
            mac_address, capabilities, registration_source, created_at, updated_at
        FROM sensor_registration_backup
    ''')
    
    # 5. Recreate indexes
    logger.info("Recreating indexes...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_registration_sensor_id 
        ON SensorRegistration(sensor_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_registration_status 
        ON SensorRegistration(status)
    ''')
    
    # 6. Drop backup
    cursor.execute('DROP TABLE sensor_registration_backup')
    
    logger.info("Foreign key constraint removed successfully")


def rollback_migration(cursor):
    """Rollback the migration if needed."""
    logger.warning("Cannot easily rollback this migration - table structure changed")


def main():
    """Main migration execution."""
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    try:
        logger.info(f"Connecting to database: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if migration already applied
        if migration_already_applied(cursor):
            logger.info("Migration already applied - skipping")
            return 0
        
        # Apply migration
        apply_migration(cursor)
        
        # Record migration in schema_migrations table
        cursor.execute('''
            INSERT INTO schema_migrations (migration_name, applied_at)
            VALUES (?, ?)
        ''', (Path(__file__).name, datetime.now().isoformat()))
        
        conn.commit()
        logger.info("Migration completed successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return 1
        
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    sys.exit(main())
