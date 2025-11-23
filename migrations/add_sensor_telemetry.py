#!/usr/bin/env python3
"""
Migration: Add SensorTelemetry table for real-time sensor data plotting
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_add_sensor_telemetry(db_path):
    """
    Create SensorTelemetry table
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SensorTelemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                data TEXT NOT NULL, -- JSON data
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
            );
        ''')
        
        # Create index for faster retrieval by sensor_id and timestamp
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time ON SensorTelemetry(sensor_id, timestamp DESC)')
        
        conn.commit()
        logger.info("Successfully created SensorTelemetry table")
        
    except Exception as e:
        logger.error(f"Error creating SensorTelemetry table: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path to import config if needed
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # from app.config import Config
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'data', 'template.db')
    # Check if db exists in app/data or just data
    if not os.path.exists(os.path.dirname(db_path)):
         db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template.db')

    migrate_add_sensor_telemetry(db_path)
