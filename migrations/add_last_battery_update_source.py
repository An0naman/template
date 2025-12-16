#!/usr/bin/env python3
"""
Migration: Add last_battery_update_source column to SensorRegistration
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_add_last_battery_update_source(db_path):
    """
    Add last_battery_update_source column to SensorRegistration table
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(SensorRegistration)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'last_battery_update_source' not in columns:
            cursor.execute('ALTER TABLE SensorRegistration ADD COLUMN last_battery_update_source TEXT')
            conn.commit()
            logger.info("Successfully added last_battery_update_source column to SensorRegistration")
        else:
            logger.info("Column last_battery_update_source already exists in SensorRegistration")
            
    except Exception as e:
        logger.error(f"Error adding last_battery_update_source column: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path to import config if needed
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Default path for manual run
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template.db')
    
    logging.basicConfig(level=logging.INFO)
    migrate_add_last_battery_update_source(db_path)
