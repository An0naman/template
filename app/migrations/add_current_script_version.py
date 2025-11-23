#!/usr/bin/env python3
"""
Migration: Add current_script_version to SensorRegistration
===========================================================

Created: 2025-11-23
Description: Adds field to track which script version is currently running on the sensor
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
        cursor.execute("PRAGMA table_info(SensorRegistration)")
        columns = [row[1] for row in cursor.fetchall()]
        return 'current_script_version' in columns
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return False

def apply_migration(conn, cursor):
    """Apply the migration"""
    try:
        logger.info("Adding current_script_version and current_script_id to SensorRegistration...")
        
        # Add current_script_version column
        cursor.execute('''
            ALTER TABLE SensorRegistration
            ADD COLUMN current_script_version TEXT
        ''')
        
        # Add current_script_id column to link to the running script
        cursor.execute('''
            ALTER TABLE SensorRegistration
            ADD COLUMN current_script_id INTEGER
        ''')
        
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
            logger.info("Migration add_current_script_version.py already applied, skipping...")
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
