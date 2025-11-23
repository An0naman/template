#!/usr/bin/env python3
"""
Migration: Add Script Version Tracking to SensorRegistration
============================================================

Created: 2025-11-23

Description: Adds current_script_id and current_script_version fields to 
             SensorRegistration table to track what script version each sensor
             is currently running.

Usage:
------
This migration will be automatically run by docker-entrypoint.sh on container startup.
You can also run it manually:
    python app/migrations/add_script_version_tracking.py
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
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(SensorRegistration)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'current_script_version' in columns:
            return True
            
        # Also check schema_migrations table
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
    
    logger.info("Adding script version tracking columns to SensorRegistration...")
    
    try:
        # Add current_script_id column
        cursor.execute('''
            ALTER TABLE SensorRegistration 
            ADD COLUMN current_script_id INTEGER
        ''')
        logger.info("Added current_script_id column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
        logger.info("current_script_id column already exists")
    
    try:
        # Add current_script_version column
        cursor.execute('''
            ALTER TABLE SensorRegistration 
            ADD COLUMN current_script_version TEXT
        ''')
        logger.info("Added current_script_version column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
        logger.info("current_script_version column already exists")
    
    logger.info("Script version tracking migration completed successfully")


def rollback_migration(cursor):
    """Rollback the migration if needed."""
    
    logger.warning("Cannot rollback - SQLite does not support DROP COLUMN")
    logger.warning("To rollback, you would need to recreate the table without these columns")


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
