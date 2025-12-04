#!/usr/bin/env python3
"""
Migration: Add Check-in Interval to SensorRegistration
======================================================

Created: 2025-12-05
Description: Adds check_in_interval column to SensorRegistration table to allow
             configuring hibernation duration per device.
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
    
    logger.info("Adding check_in_interval column to SensorRegistration...")
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(SensorRegistration)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'check_in_interval' not in columns:
        cursor.execute('''
            ALTER TABLE SensorRegistration
            ADD COLUMN check_in_interval INTEGER DEFAULT 60
        ''')
        logger.info("Added check_in_interval column")
    else:
        logger.info("check_in_interval column already exists")


def rollback_migration(cursor):
    """Rollback the migration if needed."""
    
    logger.info("Rolling back check_in_interval migration...")
    # SQLite doesn't support DROP COLUMN easily in older versions, 
    # but we can ignore it for rollback in this context as it's additive
    logger.warning("Rollback for ADD COLUMN is not fully supported in SQLite without table recreation. Skipping.")


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
