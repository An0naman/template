"""
Migration: Add battery calibration columns to SensorRegistration

This migration adds support for battery voltage divider calibration
allowing users to set R1/R2 values and calibrated voltage readings.
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Migration metadata
MIGRATION_ID = 'add_battery_calibration'
MIGRATION_DATE = '2026-01-05'
MIGRATION_DESCRIPTION = 'Add battery_r1, battery_r2, and battery_calibrated_voltage columns to SensorRegistration'


def check_if_applied(cursor):
    """Check if this migration has already been applied."""
    try:
        cursor.execute("SELECT 1 FROM schema_migrations WHERE migration_name = ?", (MIGRATION_ID,))
        return cursor.fetchone() is not None
    except sqlite3.OperationalError:
        # schema_migrations table doesn't exist
        return False


def apply_migration(cursor):
    """Apply the actual migration changes."""
    
    logger.info("Checking SensorRegistration table for battery calibration columns...")
    
    # Check what columns exist
    cursor.execute("PRAGMA table_info(SensorRegistration)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Add battery_r1 if it doesn't exist
    if 'battery_r1' not in existing_columns:
        logger.info("Adding battery_r1 column...")
        cursor.execute('ALTER TABLE SensorRegistration ADD COLUMN battery_r1 REAL DEFAULT 100000.0')
        logger.info("✓ Added battery_r1 column")
    else:
        logger.info("Column battery_r1 already exists, skipping")
    
    # Add battery_r2 if it doesn't exist
    if 'battery_r2' not in existing_columns:
        logger.info("Adding battery_r2 column...")
        cursor.execute('ALTER TABLE SensorRegistration ADD COLUMN battery_r2 REAL DEFAULT 100000.0')
        logger.info("✓ Added battery_r2 column")
    else:
        logger.info("Column battery_r2 already exists, skipping")
    
    # Add battery_calibrated_voltage if it doesn't exist
    if 'battery_calibrated_voltage' not in existing_columns:
        logger.info("Adding battery_calibrated_voltage column...")
        cursor.execute('ALTER TABLE SensorRegistration ADD COLUMN battery_calibrated_voltage REAL')
        logger.info("✓ Added battery_calibrated_voltage column")
    else:
        logger.info("Column battery_calibrated_voltage already exists, skipping")
    
    # Add battery_calibration_date if it doesn't exist
    if 'battery_calibration_date' not in existing_columns:
        logger.info("Adding battery_calibration_date column...")
        cursor.execute('ALTER TABLE SensorRegistration ADD COLUMN battery_calibration_date TIMESTAMP')
        logger.info("✓ Added battery_calibration_date column")
    else:
        logger.info("Column battery_calibration_date already exists, skipping")
    
    logger.info("Battery calibration columns migration completed successfully!")


def record_migration(cursor):
    """Record that this migration has been applied."""
    cursor.execute('''
        INSERT OR REPLACE INTO schema_migrations (migration_name, applied_at)
        VALUES (?, datetime('now'))
    ''', (MIGRATION_ID,))


def run_migration(db_path):
    """
    Main entry point for running this migration.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create migrations table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                execution_time_ms INTEGER
            )
        ''')
        
        # Check if already applied
        if check_if_applied(cursor):
            logger.info(f"Migration {MIGRATION_ID} already applied, skipping...")
            return True
        
        logger.info(f"Applying migration: {MIGRATION_ID}")
        apply_migration(cursor)
        record_migration(cursor)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Migration {MIGRATION_ID} completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error applying migration {MIGRATION_ID}: {e}", exc_info=True)
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == '__main__':
    # For testing
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = 'data/app_data.db'
    
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
