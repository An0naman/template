#!/usr/bin/env python3
"""
Migration: Add Sensor Master Control Tables
==========================================

Created: 2025-11-21
Description: Creates tables for Sensor Master Control functionality that allows
             sensors (like ESP32s) to "phone home" and receive configuration instructions
             from a designated master control instance.

Tables:
-------
1. SensorMasterControl - Stores master control instance configurations
2. SensorRegistration - Tracks registered sensors and their assignments
3. SensorMasterConfig - Stores configuration templates for different sensor types

Usage:
------
This migration will be automatically run by docker-entrypoint.sh on container startup.
You can also run it manually:
    python app/migrations/add_sensor_master_control.py
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
        if "no such table: schema_migrations" in str(e):
            logger.warning("schema_migrations table not found - run 000_init_migration_tracking.py first")
            return False
        raise


def apply_migration(cursor):
    """Apply the actual migration changes."""
    
    logger.info("Creating SensorMasterControl table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorMasterControl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_name TEXT NOT NULL UNIQUE,
            description TEXT,
            api_endpoint TEXT,
            api_key TEXT,
            is_enabled BOOLEAN DEFAULT 0,
            priority INTEGER DEFAULT 100,
            last_heartbeat TIMESTAMP,
            status TEXT DEFAULT 'inactive',
            max_sensors INTEGER DEFAULT 0,
            allowed_sensor_types TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    logger.info("Creating SensorRegistration table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorRegistration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL UNIQUE,
            sensor_name TEXT,
            sensor_type TEXT NOT NULL,
            hardware_info TEXT,
            firmware_version TEXT,
            assigned_master_id INTEGER,
            config_hash TEXT,
            last_check_in TIMESTAMP,
            last_config_update TIMESTAMP,
            status TEXT DEFAULT 'pending',
            ip_address TEXT,
            mac_address TEXT,
            capabilities TEXT,
            registration_source TEXT DEFAULT 'auto',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_master_id) REFERENCES SensorMasterControl(id) ON DELETE SET NULL
        )
    ''')
    
    logger.info("Creating SensorMasterConfig table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorMasterConfig (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_id INTEGER NOT NULL,
            sensor_id TEXT,
            sensor_type TEXT,
            config_name TEXT NOT NULL,
            config_data TEXT NOT NULL,
            config_version INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 100,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (master_id) REFERENCES SensorMasterControl(id) ON DELETE CASCADE,
            FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
        )
    ''')
    
    logger.info("Creating SensorCommandQueue table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorCommandQueue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            command_type TEXT NOT NULL,
            command_data TEXT,
            priority INTEGER DEFAULT 100,
            status TEXT DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
        )
    ''')
    
    logger.info("Creating indexes for Sensor Master Control tables...")
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_registration_sensor_id 
        ON SensorRegistration(sensor_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_registration_assigned_master 
        ON SensorRegistration(assigned_master_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_registration_status 
        ON SensorRegistration(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_master_config_sensor 
        ON SensorMasterConfig(sensor_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_master_config_master 
        ON SensorMasterConfig(master_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_command_queue_sensor 
        ON SensorCommandQueue(sensor_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_command_queue_status 
        ON SensorCommandQueue(status)
    ''')
    
    logger.info("Creating default master control configuration...")
    cursor.execute('''
        INSERT OR IGNORE INTO SensorMasterControl 
        (instance_name, description, is_enabled, status, priority)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'Local Master',
        'Default local master control instance',
        0,  # Disabled by default
        'inactive',
        1  # Highest priority
    ))
    
    logger.info("Sensor Master Control tables created successfully")


def rollback_migration(cursor):
    """Rollback the migration if needed."""
    
    logger.info("Rolling back Sensor Master Control migration...")
    
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_command_queue_status')
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_command_queue_sensor')
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_master_config_master')
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_master_config_sensor')
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_registration_status')
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_registration_assigned_master')
    cursor.execute('DROP INDEX IF EXISTS idx_sensor_registration_sensor_id')
    
    cursor.execute('DROP TABLE IF EXISTS SensorCommandQueue')
    cursor.execute('DROP TABLE IF EXISTS SensorMasterConfig')
    cursor.execute('DROP TABLE IF EXISTS SensorRegistration')
    cursor.execute('DROP TABLE IF EXISTS SensorMasterControl')
    
    logger.info("Sensor Master Control migration rolled back")


def main():
    """Main migration execution."""
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")
    
    conn = None
    try:
        logger.info(f"Connecting to database: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if migration already applied
        if migration_already_applied(cursor):
            logger.info(f"Migration {Path(__file__).name} already applied, skipping...")
            return 0
        
        logger.info(f"Applying migration: {Path(__file__).name}")
        
        # Apply migration
        apply_migration(cursor)
        
        # Record migration
        cursor.execute("""
            INSERT INTO schema_migrations (migration_name, applied_at)
            VALUES (?, ?)
        """, (Path(__file__).name, datetime.now().isoformat()))
        
        conn.commit()
        logger.info(f"Migration {Path(__file__).name} applied successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error applying migration: {e}", exc_info=True)
        if conn:
            conn.rollback()
            logger.info("Changes rolled back")
        return 1
        
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    sys.exit(main())
