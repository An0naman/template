#!/usr/bin/env python3
"""
Migration: Add board_type column to SensorRegistration
======================================================

Created: 2025-12-26

Description: Adds board_type column to track the specific ESP32 board type
             (e.g., esp32_wroom32, firebeetle2_esp32c6) being used by each sensor.

This allows the Sensor Master Control system to:
- Track which board variant is running the firmware
- Display board-specific information in the UI
- Provide board-specific configuration and documentation

Usage:
------
This migration will be automatically run by docker-entrypoint.sh on container startup.
You can also run it manually:
    python app/migrations/add_board_type_column.py
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

# Get database path from environment or use default
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')


def migration_already_applied(cursor) -> bool:
    """Check if this migration has already been applied."""
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(SensorRegistration)")
        columns = [row[1] for row in cursor.fetchall()]
        return 'board_type' in columns
    except sqlite3.OperationalError as e:
        logger.error(f"Error checking migration status: {e}")
        return False


def apply_migration(cursor):
    """Apply the actual migration changes."""
    
    logger.info("Adding board_type column to SensorRegistration table...")
    
    try:
        # Add board_type column
        cursor.execute('''
            ALTER TABLE SensorRegistration
            ADD COLUMN board_type TEXT
        ''')
        
        logger.info("✓ Added board_type column")
        
        # Update existing records to have a default board_type based on sensor_type
        # If sensor_type contains "c6", mark as firebeetle2_esp32c6, otherwise esp32_wroom32
        cursor.execute('''
            UPDATE SensorRegistration
            SET board_type = CASE
                WHEN sensor_type LIKE '%c6%' THEN 'firebeetle2_esp32c6'
                WHEN sensor_type LIKE '%firebeetle%' THEN 'firebeetle2_esp32c6'
                ELSE 'esp32_wroom32'
            END
            WHERE board_type IS NULL
        ''')
        
        updated_count = cursor.rowcount
        if updated_count > 0:
            logger.info(f"✓ Updated {updated_count} existing sensor(s) with default board_type")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.info("Column already exists, skipping...")
        else:
            raise


def record_migration(cursor):
    """Record this migration in the schema_migrations table."""
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO schema_migrations (migration_name, applied_at)
            VALUES (?, CURRENT_TIMESTAMP)
        """, (Path(__file__).name,))
        logger.info(f"✓ Recorded migration: {Path(__file__).name}")
    except sqlite3.OperationalError as e:
        logger.warning(f"Could not record migration: {e}")


def main():
    """Main migration execution."""
    logger.info("="*60)
    logger.info("Migration: Add board_type column")
    logger.info("="*60)
    
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"Database not found at: {DATABASE_PATH}")
        logger.error("Please ensure the database exists before running migrations.")
        return 1
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if migration already applied
        if migration_already_applied(cursor):
            logger.info("Migration already applied. Skipping...")
            conn.close()
            return 0
        
        # Apply migration
        apply_migration(cursor)
        
        # Record migration
        record_migration(cursor)
        
        # Commit changes
        conn.commit()
        logger.info("✓ Migration completed successfully!")
        
        conn.close()
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
