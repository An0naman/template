#!/usr/bin/env python3
"""
Migration: Add last_executed column to SensorScripts
====================================================

Created: 2025-11-23
Description: Adds last_executed timestamp to track when ESP32 last ran a script
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database path, handling both Docker and local environments"""
    if os.path.exists('/app/data'):
        return '/app/data/template.db'
    
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / 'template.db')

def migration_already_applied(cursor):
    """Check if migration has already been applied"""
    try:
        cursor.execute("PRAGMA table_info(SensorScripts)")
        columns = [row[1] for row in cursor.fetchall()]
        return 'last_executed' in columns
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return False

def apply_migration(conn, cursor):
    """Apply the migration"""
    try:
        logger.info("Adding last_executed column to SensorScripts table...")
        
        # Add last_executed column
        cursor.execute('''
            ALTER TABLE SensorScripts
            ADD COLUMN last_executed TEXT
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
            logger.info("Migration add_script_last_executed.py already applied, skipping...")
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
