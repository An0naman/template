#!/usr/bin/env python3
"""
Migration: Initialize migration tracking system
Created: 2025-10-30
Description: Creates the schema_migrations table to track which migrations have been applied.
             This should be the first migration in any new app instance.
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
    """
    Check if the schema_migrations table already exists.
    """
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking if migration applied: {e}")
        return False


def apply_migration(cursor):
    """
    Create the schema_migrations table for tracking applied migrations.
    """
    logger.info("Creating schema_migrations table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            execution_time_ms INTEGER
        )
    """)
    
    # Create an index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_migration_name 
        ON schema_migrations(migration_name)
    """)
    
    logger.info("✓ schema_migrations table created successfully")


def record_migration(cursor, migration_name: str, success: bool = True, error_msg: str = None):
    """
    Record this migration in the tracking table.
    """
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO schema_migrations 
            (migration_name, success, error_message) 
            VALUES (?, ?, ?)
        """, (migration_name, success, error_msg))
    except Exception as e:
        logger.error(f"Failed to record migration: {e}")


def main():
    """
    Main migration execution function.
    """
    migration_name = Path(__file__).name
    start_time = datetime.now()
    
    logger.info(f"Starting migration: {migration_name}")
    logger.info(f"Database path: {DATABASE_PATH}")
    
    # Ensure database directory exists
    db_dir = Path(DATABASE_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if migration already applied
        if migration_already_applied(cursor):
            logger.info("✓ schema_migrations table already exists, skipping...")
            return 0
        
        # Apply migration
        logger.info("Applying migration...")
        apply_migration(cursor)
        
        # Record this migration (after table is created)
        record_migration(cursor, migration_name, success=True)
        
        # Commit changes
        conn.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✓ Migration completed successfully in {execution_time:.2f}ms")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return 1
        
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
