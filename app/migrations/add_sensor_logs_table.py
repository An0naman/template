#!/usr/bin/env python3
"""
Migration: Add Sensor Logs Table
===============================

Created: 2025-11-24
Description: Creates SensorLogs table for storing remote logs from sensors.

Tables:
-------
1. SensorLogs - Stores log messages from sensors

Usage:
------
Run manually:
    python app/migrations/add_sensor_logs_table.py
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
            # If schema_migrations doesn't exist, we can't track migrations
            # But we can check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SensorLogs'")
            return cursor.fetchone() is not None
        raise


def apply_migration(cursor):
    """Apply the actual migration changes."""
    
    logger.info("Creating SensorLogs table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            message TEXT NOT NULL,
            log_level TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
        )
    ''')
    
    logger.info("Creating index for SensorLogs...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sensor_logs_sensor_time 
        ON SensorLogs(sensor_id, created_at)
    ''')
    
    logger.info("SensorLogs table created successfully")


def main():
    """Main migration execution."""
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
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
        
        # Record migration if schema_migrations exists
        try:
            cursor.execute("""
                INSERT INTO schema_migrations (migration_name, applied_at)
                VALUES (?, ?)
            """, (Path(__file__).name, datetime.now().isoformat()))
        except sqlite3.OperationalError:
            logger.warning("schema_migrations table not found - migration applied but not tracked")
        
        conn.commit()
        logger.info(f"Migration {Path(__file__).name} applied successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Error applying migration: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return 1
        
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    sys.exit(main())
