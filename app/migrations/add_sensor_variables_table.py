#!/usr/bin/env python3
"""
Migration: Add SensorVariables table for persistent variable storage
Description: Creates a table to store sensor variables that persist through hibernation
Author: System
Date: 2026-01-04
"""

import sqlite3
import sys
import os

# Add parent directory to path to import db module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_migration_id():
    """Return a unique identifier for this migration"""
    return "add_sensor_variables_table_20260104"

def check_if_applied(cursor):
    """Check if this migration has already been applied"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='SensorVariables'
    """)
    return cursor.fetchone() is not None

def apply_migration(conn):
    """Apply the migration"""
    cursor = conn.cursor()
    
    # Check if already applied
    if check_if_applied(cursor):
        print("✓ Migration already applied: SensorVariables table exists")
        return True
    
    print("Applying migration: Creating SensorVariables table...")
    
    # Create SensorVariables table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SensorVariables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL UNIQUE,
            variables TEXT NOT NULL,  -- JSON blob of variables
            updated_at TEXT NOT NULL,
            FOREIGN KEY (sensor_id) REFERENCES SensorRegistration(sensor_id) ON DELETE CASCADE
        )
    """)
    
    # Create index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensor_variables_sensor_id 
        ON SensorVariables(sensor_id)
    """)
    
    conn.commit()
    print("✓ SensorVariables table created successfully")
    
    # Track this migration (if MigrationHistory table exists)
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO MigrationHistory (migration_id, applied_at)
            VALUES (?, datetime('now'))
        """, (get_migration_id(),))
        conn.commit()
    except sqlite3.OperationalError:
        # MigrationHistory table doesn't exist, skip tracking
        print("  (Migration tracking skipped - MigrationHistory table not found)")
    
    return True

def rollback_migration(conn):
    """Rollback the migration"""
    cursor = conn.cursor()
    
    print("Rolling back migration: Dropping SensorVariables table...")
    
    cursor.execute("DROP TABLE IF EXISTS SensorVariables")
    cursor.execute("DROP INDEX IF EXISTS idx_sensor_variables_sensor_id")
    
    # Remove from migration history
    cursor.execute("""
        DELETE FROM MigrationHistory 
        WHERE migration_id = ?
    """, (get_migration_id(),))
    
    conn.commit()
    print("✓ Migration rolled back successfully")
    return True

def main():
    """Main function for standalone execution"""
    # Direct database connection without Flask context
    db_path = os.environ.get('DATABASE_PATH', '/app/data/template.db')
    
    if not os.path.exists(db_path):
        print(f"✗ Database not found at {db_path}")
        sys.exit(1)
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        success = rollback_migration(conn)
    else:
        success = apply_migration(conn)
    
    conn.close()
    
    if success:
        print("✓ Migration completed successfully")
        sys.exit(0)
    else:
        print("✗ Migration failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
